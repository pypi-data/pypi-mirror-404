from typing import Dict, Any, Optional
from langchain_core.runnables import RunnableConfig
from langfuse.langchain import CallbackHandler as LangfuseCallbackHandler
from ..callbacks.async_langfuse_handler import AsyncLangfuseCallbackHandler

# Singleton holder for the Langfuse handler to avoid multiple instances per run
_LANGFUSE_HANDLER: Optional[LangfuseCallbackHandler] = None
_ASYNC_LANGFUSE_HANDLER: Optional[AsyncLangfuseCallbackHandler] = None

def _get_langfuse_handler() -> LangfuseCallbackHandler:
    global _LANGFUSE_HANDLER
    if _LANGFUSE_HANDLER is None:
        _LANGFUSE_HANDLER = LangfuseCallbackHandler()
    return _LANGFUSE_HANDLER

def get_langfuse_handler() -> LangfuseCallbackHandler:
    return _get_langfuse_handler()

def get_async_langfuse_handler() -> "AsyncLangfuseCallbackHandler":
    """
    Returns a singleton instance of the async Langfuse handler, ensuring it
    shares the same underlying synchronous Langfuse handler singleton.
    """
    global _ASYNC_LANGFUSE_HANDLER
    if _ASYNC_LANGFUSE_HANDLER is None:
        sync_handler = get_langfuse_handler()
        _ASYNC_LANGFUSE_HANDLER = AsyncLangfuseCallbackHandler(sync_handler=sync_handler)
    return _ASYNC_LANGFUSE_HANDLER

def prepare_trace_config(context: Dict[str, Any]) -> RunnableConfig:
    """
    Prepares a minimal RunnableConfig for tracing, primarily for Langfuse.

    - Creates a new config containing only tracing-related information.
    - Extracts 'trace_metadata' from the context's 'configurable' dict
      and uses it as the 'metadata' for the new trace config.
    - Adds a singleton Langfuse callback handler.
    """
    # The full config is passed in the 'config' key of the context
    # Start with a copy of the existing config from the graph to preserve its state
    run_config = context.get("config", {}).copy()

    # Extract trace_metadata from the 'configurable' part of the full config
    trace_metadata = run_config.get("trace_metadata", {})
    if not trace_metadata:
        trace_metadata = run_config.get("configurable", {}).get("trace_metadata", {})

    # If trace_metadata exists, merge all its fields into the main metadata key
    if trace_metadata and isinstance(trace_metadata, dict):
        if "metadata" not in run_config:
            run_config["metadata"] = {}
        run_config["metadata"].update(trace_metadata)

    return run_config
    