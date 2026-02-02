# Feedback Management with Langfuse

This document outlines the design and implementation of the Langsmith-style feedback system using Langfuse as the backend.

## Design Approach: Parent Observation for Feedback Groups

To replicate the grouped feedback functionality seen in Langsmith, we use Langfuse's hierarchical tracing structure. This approach is called the "Parent Observation" model.

-   **Feedback Group**: A batch of feedback items submitted together (e.g., a user rating multiple aspects of a response) is represented as a single **`Span`** (also called an Observation) in Langfuse. This `Span` acts as a container for the group.
-   **Group-Level Data**: All metadata that applies to the entire group, such as `correction` data or a unique `feedback_group_id`, is stored in the `metadata` of this parent `Span`.
-   **Individual Feedback**: Each individual feedback item (e.g., "helpfulness: 0.9", "safety: true") is represented as a **`Score`** object.
-   **Linking**: Crucially, each `Score` is linked to the parent `Span` via its `observation_id`. This creates the hierarchy that is visible in the Langfuse UI.

This design provides a clean UI representation and a semantically correct data model.

### Example

A user submits feedback for a chatbot response (`run_id: "trace-123"`):
-   **Helpfulness**: 9/10
-   **Safety**: Safe (True)
-   **Correction**: The answer should have included details about X.

This is modeled in Langfuse as:

1.  A **`Span`** is created in trace `trace-123`.
    -   `name`: "user-feedback-group"
    -   `metadata`: `{ "feedback_group_id": "fg-abc", "correction": { "expected": "..." } }`
    -   This span gets a unique `observation_id`, e.g., `"obs-xyz"`.
2.  Two **`Score`** objects are created:
    -   Score 1:
        -   `name`: "helpfulness"
        -   `value`: `0.9`
        -   `trace_id`: "trace-123"
        -   `observation_id`: `"obs-xyz"` (links to the parent span)
    -   Score 2:
        -   `name`: "safety"
        -   `value`: `1.0` (boolean `True` is converted)
        -   `trace_id`: "trace-123"
        -   `observation_id`: `"obs-xyz"` (links to the parent span)

## Data Mapping: Langfuse API to `FeedbackOut` Schema

The `read_feedback` method in `LangfuseFeedbackManager` fetches data from multiple Langfuse objects and combines them into a single, consistent `FeedbackOut` Pydantic model.

| `FeedbackOut` Field   | Source of Data                                   | Example Value                                  |
| --------------------- | ------------------------------------------------ | ---------------------------------------------- |
| `feedback_id`         | `score.id`                                       | `'sc-12345'`                                   |
| `run_id`              | `score.trace_id`                                 | `'tr-abcde'`                                   |
| `key`                 | `score.name`                                     | `'helpfulness'`                                |
| `score`               | `score.value`                                    | `0.9`                                          |
| `value`               | `score.metadata.get('value_dict')` or `score.value` | `{'direction': 'up'}` or `'up'`                |
| `comment`             | `score.comment`                                  | `'Very helpful.'`                              |
| `created_at`          | `score.timestamp`                                | `datetime.datetime(...)`                       |
| `correction`          | `parent_observation.metadata.get('correction')`  | `{'expected': 'A perfect answer.'}`            |
| `feedback_group_id`   | `parent_observation.metadata.get('feedback_group_id')` | `'fg-xyz-789'`                                 |