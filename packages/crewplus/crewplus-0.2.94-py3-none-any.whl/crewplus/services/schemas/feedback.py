from typing import Optional, Union, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
import datetime

class FeedbackConfig(BaseModel):
    api_url: Optional[str] = None
    api_key: Optional[str] = None

class FeedbackIn(BaseModel):
    run_id: Union[UUID, str]
    key: str
    score: Optional[Union[float, int, bool]] = None
    value: Optional[Union[float, int, bool, str, Dict]] = None
    correction: Optional[Dict] = None
    comment: Optional[str] = None
    feedback_group_id: Optional[Union[UUID, str]] = None
    config: Optional[FeedbackConfig] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "run_id": "5323d917-f337-42c2-8437-22e6fa623930",
                "key": "accuracy",
                "score": 0.95,
                "value": "yes",
                "correction": {"expected": "correct answer"},
                "comment": "The model performed well on this task.",
                "feedback_group_id": "123e4567-e89b-12d3-a456-426614174000",
                "config": {
                    "api_url": "https://api.smith.langchain.com",
                    "api_key": "your_api_key_here"
                }
            }
        }
    )

class FeedbackUpdate(BaseModel):
    score: Optional[Union[float, int, bool]] = None
    value: Optional[Union[float, int, bool, str, Dict]] = None
    correction: Optional[Dict] = None
    comment: Optional[str] = None
    config: Optional[FeedbackConfig] = None


class FeedbackOut(BaseModel):
    """
    Represents a retrieved feedback item, including its unique ID and group context.
    This corresponds to a Langfuse Score object enriched with its parent's metadata.
    """
    feedback_id: str = Field(..., description="The unique identifier for the feedback item (maps to Langfuse score ID).")
    run_id: str = Field(..., description="The ID of the run (trace) this feedback belongs to.")
    key: str = Field(..., description="The name of the feedback key.")
    score: Optional[Union[float, int, bool, str]] = Field(None, description="The numerical or string score of the feedback.")
    value: Optional[Any] = Field(None, description="The original value of the feedback, which could be a dict or other type.")
    comment: Optional[str] = Field(None, description="The feedback comment.")
    correction: Optional[Dict] = Field(None, description="Correction data from the parent observation.")
    feedback_group_id: Optional[str] = Field(None, description="The ID of the group this feedback belongs to.")
    created_at: datetime.datetime = Field(..., description="The timestamp when the feedback was created.")

    model_config = ConfigDict(from_attributes=True)
