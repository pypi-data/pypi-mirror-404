# File: crewplus/services/tracing_manager.py

from typing import Any, Optional, List, Protocol, Dict
import os
import logging

# Langfuse imports with graceful fallback. This allows the application to run
# even if the langfuse library is not installed.
try:
    from langfuse.langchain import CallbackHandler as LangfuseCallbackHandler
    from ..callbacks.async_langfuse_handler import AsyncLangfuseCallbackHandler
    from ..utils.tracing_util import get_langfuse_handler, get_async_langfuse_handler
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    LangfuseCallbackHandler = None
    AsyncLangfuseCallbackHandler = None
    get_langfuse_handler = None
    get_async_langfuse_handler = None

class TracingContext(Protocol):
    """
    A protocol that defines a formal contract for a model to be "traceable."

    This protocol ensures that any class using the TracingManager provides the
    necessary attributes and methods for the manager to function correctly. By
    using a Protocol, we leverage Python's static analysis tools (like mypy)
    to enforce this contract, preventing runtime errors and making the system
    more robust and self-documenting.

    It allows the TracingManager to be completely decoupled from any specific
    model implementation, promoting clean, compositional design.

    A class that implements this protocol must provide:
    - A `logger` attribute for logging.
    - An `enable_tracing` attribute to control tracing.
    - A `get_model_identifier` method to describe itself for logging purposes.
    """
    logger: logging.Logger
    enable_tracing: Optional[bool]
    
    def get_model_identifier(self) -> str:
        """
        Return a string that uniquely identifies the model instance for logging.
        
        Example:
            "GeminiChatModel (model='gemini-1.5-flash')"
            
        Note:
            The '...' (Ellipsis) is the standard way in a Protocol to indicate
            that this method must be implemented by any class that conforms to
            this protocol, but has no implementation in the protocol itself.
        """
        ...

class TracingManager:
    """
    Manages the initialization and injection of tracing handlers for chat models.
    
    This class uses a composition-based approach, taking a context object that
    fulfills the TracingContext protocol. This design is highly extensible,
    allowing new tracing providers (e.g., Helicone, OpenTelemetry) to be added
    with minimal, isolated changes.
    """
    
    def __init__(self, context: TracingContext):
        """
        Args:
            context: An object (typically a chat model instance) that conforms
                     to the TracingContext protocol.
        """
        self.context = context
        self._sync_handlers: List[Any] = []
        self._async_handlers: List[Any] = []
        self._initialize_handlers()
    
    def _initialize_handlers(self):
        """
        Initializes all supported tracing handlers. This is the central point
        for adding new observability tools.
        """
        self._sync_handlers = []
        self._async_handlers = []
        self._initialize_langfuse()
        # To add a new handler (e.g., Helicone), you would add a call to
        # self._initialize_helicone() here.
    
    def _initialize_langfuse(self):
        """Initializes the Langfuse handler if it's available and enabled."""
        self.context.logger.debug("Attempting to initialize Langfuse handlers.")
        if not LANGFUSE_AVAILABLE:
            if self.context.enable_tracing is True:
                self.context.logger.warning("Langfuse is not installed; tracing will be disabled. Install with: pip install langfuse")
            else:
                self.context.logger.debug("Langfuse is not installed, skipping handler initialization.")
            return
        
        # Determine if Langfuse should be enabled via an explicit flag or
        # by detecting its environment variables.
        enable_langfuse = self.context.enable_tracing
        if enable_langfuse is None: # Auto-detect if not explicitly set
            langfuse_env_vars = ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"]
            enable_langfuse = any(os.getenv(var) for var in langfuse_env_vars)
        
        if enable_langfuse:
            try:
                # Create both sync and async handlers. We'll pick one at runtime.
                sync_handler = get_langfuse_handler()
                self._sync_handlers.append(sync_handler)

                if AsyncLangfuseCallbackHandler:
                    async_handler = get_async_langfuse_handler()
                    self._async_handlers.append(async_handler)
                
                self.context.logger.info(f"Langfuse tracing enabled for {self.context.get_model_identifier()}")
            except Exception as e:
                self.context.logger.warning(f"Failed to initialize Langfuse: {e}", exc_info=True)
        else:
            self.context.logger.info("Langfuse is not enabled, skipping handler initialization.")
    
    def add_callbacks_to_config(self, config: Optional[dict], handlers: List[Any]) -> dict:
        """A generic helper to add a list of handlers to a config object."""
        if config is None:
            config = {}
        
        self.context.logger.debug(f"Adding callbacks to config. Have {len(handlers)} handlers to add.")

        if not handlers or config.get("metadata", {}).get("tracing_disabled"):
            self.context.logger.debug("No handlers to add or tracing is disabled for this run.")
            return config
        
        callbacks = config.get("callbacks")
        
        if hasattr(callbacks, 'add_handler') and hasattr(callbacks, 'handlers'):
            # This block is for CallbackManager instances
            self.context.logger.debug(f"Config has a CallbackManager with {len(callbacks.handlers)} existing handlers.")
            for handler in handlers:
                if not any(isinstance(cb, type(handler)) for cb in callbacks.handlers):
                    callbacks.add_handler(handler, inherit=True)
            self.context.logger.debug(f"CallbackManager now has {len(callbacks.handlers)} handlers.")
            return config
        
        # This block is for simple lists of callbacks
        current_callbacks = callbacks or []
        self.context.logger.debug(f"Config has a list with {len(current_callbacks)} existing callbacks.")
        new_callbacks = list(current_callbacks)
        
        for handler in handlers:
            if not any(isinstance(cb, type(handler)) for cb in new_callbacks):
                new_callbacks.append(handler)
        
        if len(new_callbacks) > len(current_callbacks):
            # Create a new dictionary with the updated callbacks list.
            # This is a safe operation that overwrites the existing 'callbacks'
            # key and avoids mutating the original config object.
            return {**config, "callbacks": new_callbacks}
        
        return config

    def add_sync_callbacks_to_config(self, config: Optional[dict], handlers: Optional[List[Any]] = None) -> dict:
        """
        Adds synchronous tracing handlers to the request configuration.

        Args:
            config: The configuration dictionary to which callbacks will be added.
            handlers: An optional list of handlers to add. If not provided,
                      the manager's default synchronous handlers are used.
        """
        handlers_to_add = self._sync_handlers if handlers is None else handlers
        return self.add_callbacks_to_config(config, handlers_to_add)

    def add_async_callbacks_to_config(self, config: Optional[dict], handlers: Optional[List[Any]] = None) -> dict:
        """
        Adds asynchronous tracing handlers to the request configuration.

        Args:
            config: The configuration dictionary to which callbacks will be added.
            handlers: An optional list of handlers to add. If not provided,
                      the manager's default asynchronous handlers are used.
        """
        handlers_to_add = self._async_handlers if handlers is None else handlers
        return self.add_callbacks_to_config(config, handlers_to_add)
