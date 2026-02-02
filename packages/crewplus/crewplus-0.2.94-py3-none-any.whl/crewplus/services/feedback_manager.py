import logging
from typing import Optional, List, Union, Dict, Any
from uuid import UUID, uuid4
import datetime

from langfuse import Langfuse
from langfuse.types import TraceContext
from .schemas.feedback import FeedbackIn, FeedbackUpdate, FeedbackOut

logger = logging.getLogger(__name__)

class LangfuseFeedbackManager:
    """
    Manages CRUD operations for Langsmith-style feedback using Langfuse as the backend.
    
    This manager uses the "Parent Observation" approach, where a batch of feedback
    is represented by a parent Span, and each individual feedback item is a Score
    attached to that Span. It is designed to work with an existing trace (run).
    """

    def __init__(self, langfuse_client: Langfuse):
        """
        Initializes the feedback manager with a Langfuse client instance.

        Args:
            langfuse_client: An initialized Langfuse client.
        """
        if not langfuse_client:
            raise ValueError("A valid Langfuse client instance is required.")
        self.client = langfuse_client

    def read_feedback(self, feedback_id: str) -> Optional[FeedbackOut]:
        """
        Reads a single feedback item (a Score) and enriches it with data
        from its parent observation (the feedback group).

        Args:
            feedback_id: The unique ID of the feedback item (score).

        Returns:
            A FeedbackOut object containing the full context, or None if not found.
        """
        try:
            # Step 1: Fetch the score itself using the correct v2 client and method.
            # The get method expects a list of IDs and returns a response object.
            scores_response = self.client.api.score_v_2.get(score_ids=[feedback_id])
            if not scores_response or not scores_response.data:
                logger.warning(f"No score found for feedback_id: {feedback_id}")
                return None
            
            score = scores_response.data[0]

            correction = None
            feedback_group_id = None
            value = score.value
            run_id_to_return = score.trace_id

            # Step 2: Fetch the parent observation to get group context
            if score.observation_id:
                parent_obs = self.client.api.observations.get(observation_id=score.observation_id)
                if parent_obs.metadata:
                    correction = parent_obs.metadata.get("correction")
                    feedback_group_id = parent_obs.metadata.get("feedback_group_id")
                    original_run_id = parent_obs.metadata.get("original_run_id")
                    if original_run_id:
                        run_id_to_return = original_run_id
                
                # Check if the original value was a dict stored in the score's metadata
                if score.metadata and "value_dict" in score.metadata:
                    value = score.metadata["value_dict"]

            # Step 3: Construct the rich FeedbackOut object from the collected data.
            # This is where the raw data is parsed into your desired schema.
            return FeedbackOut(
                feedback_id=score.id,
                run_id=run_id_to_return,
                key=score.name,
                score=score.value,
                value=value,
                comment=score.comment,
                created_at=score.timestamp,
                correction=correction,
                feedback_group_id=feedback_group_id,
            )
        except Exception:
            logger.exception("Failed to read feedback with id=%s", feedback_id)
            return None

    def create_feedback_batch(self, feedbacks: List[FeedbackIn]) -> List[FeedbackOut]:
        """
        Creates a group of feedback items under a single parent observation in an existing trace.

        Args:
            feedbacks: A list of FeedbackIn objects. The `run_id`, `correction`, and 
                       `feedback_group_id` from the first item are used for the group.
        
        Returns:
            A list of FeedbackOut objects for the created feedback items.
        """
        if not feedbacks:
            return []

        first_item = feedbacks[0]
        run_id = str(first_item.run_id)
        # Convert the client's run_id to a deterministic Langfuse trace_id.
        trace_id = Langfuse.create_trace_id(seed=run_id)
        feedback_group_id = str(first_item.feedback_group_id or uuid4())
        
        group_metadata = {
            "feedback_group_id": feedback_group_id,
            "original_run_id": run_id, # Store original run_id for retrieval
        }
        if first_item.correction:
            group_metadata["correction"] = first_item.correction

        try:
            # Create the parent span within the existing trace to act as the group container.
            feedback_group_span = self.client.start_span(
                trace_context=TraceContext(trace_id=trace_id),
                name="user-feedback-group",
                metadata=group_metadata,
                input=[f.dict(exclude_unset=True) for f in feedbacks]
            )
            parent_observation_id = feedback_group_span.id

            created_feedbacks = []
            for item in feedbacks:
                score_value: Any = item.score if item.score is not None else item.value
                
                if isinstance(score_value, bool):
                    score_value = 1.0 if score_value else 0.0
                
                score_metadata = None
                value_to_return = score_value
                if isinstance(score_value, dict):
                    score_metadata = {"value_dict": score_value}
                    value_to_return = score_value
                    # Langfuse score `value` must be string or float. Set to neutral.
                    score_value = 0 

                if score_value is not None:
                    # Manually create a score ID to include it in the returned object.
                    score_id = self.client._create_observation_id()
                    self.client.create_score(
                        score_id=score_id,
                        name=item.key,
                        value=score_value,
                        trace_id=trace_id,
                        observation_id=parent_observation_id,
                        comment=item.comment,
                        metadata=score_metadata,
                    )
                    
                    feedback_out = FeedbackOut(
                        feedback_id=score_id,
                        run_id=run_id,
                        key=item.key,
                        score=score_value,
                        value=value_to_return,
                        comment=item.comment,
                        created_at=datetime.datetime.now(datetime.timezone.utc),
                        correction=group_metadata.get("correction"),
                        feedback_group_id=feedback_group_id,
                    )
                    created_feedbacks.append(feedback_out)
            
            feedback_group_span.end()
            self.client.flush()
            return created_feedbacks
        except Exception:
            logger.exception("Failed to create feedback batch for run_id=%s", run_id)
            return []

    def get_feedback_by_group_id(self, run_id: str, feedback_group_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all scores for a given feedback group ID within a trace.

        Args:
            run_id: The application-specific run ID, which will be converted to a trace ID.
            feedback_group_id: The ID of the feedback group.
        
        Returns:
            A list of score dictionaries.
        """
        try:
            trace_id = Langfuse.create_trace_id(seed=run_id)
            full_trace = self.client.api.trace.get(trace_id=trace_id)
            
            parent_obs = next(
                (obs for obs in full_trace.observations 
                 if obs.metadata and obs.metadata.get("feedback_group_id") == feedback_group_id),
                None
            )
            
            if not parent_obs:
                return []

            return [
                score.dict() for score in full_trace.scores 
                if score.observation_id == parent_obs.id
            ]
        except Exception:
            logger.exception(f"Error getting feedback for run_id {run_id} and group {feedback_group_id}")
            return []

    def delete_feedback(self, feedback_id: str) -> bool:
        """Deletes a single feedback item (a Score)."""
        try:
            self.client.api.score.delete(score_id=feedback_id)
            # Flush immediately to minimize the non-atomic window.
            self.client.flush()
            return True
        except Exception:
            logger.exception("Failed to delete feedback with id=%s", feedback_id)
            return False
            
    def update_feedback(self, feedback_id: str, update_data: FeedbackUpdate) -> bool:
        """
        Updates a feedback item (Score).

        ATTENTION: Langfuse does not support native updates for scores. This method
        simulates an update by DELETING the old score and CREATING a new one with the
        same ID to preserve client-side consistency.

        WARNING: This operation is not atomic. There is a small time window between
        deletion and creation where a read for this feedback ID will fail.

        Note: Updates to `correction` are ignored by this method, as `correction` is a 
        group-level attribute on the parent observation, which cannot be modified
        after creation via the SDK.
        """
        try:
            scores_response = self.client.api.score_v_2.get(score_ids=[feedback_id])
            if not scores_response or not scores_response.data:
                logger.warning(f"Cannot update. No score found for feedback_id: {feedback_id}")
                return False
            score_to_update = scores_response.data[0]

            if update_data.correction is not None:
                logger.warning(
                    "Updating 'correction' on an individual feedback item is not supported "
                    "as it's a group-level attribute. This field will be ignored."
                )

            # Preserve the ID by deleting and then recreating the score.
            self.delete_feedback(feedback_id)

            new_val = update_data.score if update_data.score is not None else update_data.value
            if new_val is None: new_val = score_to_update.value
            if isinstance(new_val, bool): new_val = 1.0 if new_val else 0.0

            self.client.create_score(
                score_id=feedback_id,  # Re-use the original score ID
                name=score_to_update.name,
                value=new_val,
                trace_id=score_to_update.trace_id,
                observation_id=score_to_update.observation_id,
                comment=update_data.comment or score_to_update.comment,
                metadata=score_to_update.metadata
            )
            # Flush immediately to minimize the non-atomic window.
            self.client.flush()
            
            return True
        except Exception:
            logger.exception("Failed to update feedback for id=%s", feedback_id)
            return False
