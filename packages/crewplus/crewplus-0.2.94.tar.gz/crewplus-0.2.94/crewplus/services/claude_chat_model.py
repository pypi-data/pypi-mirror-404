import os
import logging
from typing import Any, Dict, Iterator, List, Optional, AsyncIterator, Union
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_core.callbacks import (
    CallbackManagerForLLMRun,
    AsyncCallbackManagerForLLMRun
)
from pydantic import Field, SecretStr
from langchain_core.utils import convert_to_secret_str
from .tracing_manager import TracingManager, TracingContext

try:
    from anthropic import AnthropicVertex, AsyncAnthropicVertex
    ANTHROPIC_VERTEX_AVAILABLE = True
except ImportError:
    ANTHROPIC_VERTEX_AVAILABLE = False
    AnthropicVertex = None
    AsyncAnthropicVertex = None


class ClaudeChatModel(BaseChatModel):
    """Custom chat model for Claude on Vertex AI.

    This model provides a robust interface to Anthropic's Claude models via Google Vertex AI,
    maintaining compatibility with the LangChain ecosystem while leveraging Claude's advanced
    capabilities.

    It supports standard invocation, streaming, and asynchronous operations using the
    Anthropic Vertex SDK.

    **Authentication:**
    Authentication is handled via Google Cloud credentials:
    - **Application Default Credentials (ADC):** Run `gcloud auth application-default login`
    - **Service Account:** Provide `service_account_file` or set `GOOGLE_APPLICATION_CREDENTIALS`
    - The SDK automatically uses the standard `google-auth-library` flow

    **Tracing Integration:**
    Tracing (e.g., with Langfuse) is automatically enabled when the respective
    environment variables are set. For Langfuse:
    - LANGFUSE_PUBLIC_KEY: Your Langfuse public key
    - LANGFUSE_SECRET_KEY: Your Langfuse secret key
    - LANGFUSE_HOST: Langfuse host URL (optional, defaults to https://cloud.langfuse.com)

    You can also configure it explicitly or disable it. Session and user tracking
    can be set per call via metadata.

    Attributes:
        model_name (str): The Claude model to use (e.g., "claude-opus-4-5", "claude-sonnet-4-5").
        project_id (str): Google Cloud Project ID.
        location (str): Google Cloud location (e.g., "global", "us-east1", "europe-west1").
        temperature (Optional[float]): The sampling temperature for generation (0.0 to 1.0).
        max_tokens (int): The maximum number of tokens to generate.
        top_p (Optional[float]): The top-p (nucleus) sampling parameter.
        top_k (Optional[int]): The top-k sampling parameter.
        service_account_file (Optional[str]): Path to GCP service account JSON file.
        logger (Optional[logging.Logger]): An optional logger instance.
        enable_tracing (Optional[bool]): Enable/disable all tracing (auto-detect if None).

    Example:
        .. code-block:: python

            # Set Langfuse environment variables (optional)
            import os
            os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-..."
            os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-..."
            os.environ["LANGFUSE_HOST"] = "https://cloud.langfuse.com"

            from crewplus.services import ClaudeChatModel
            from langchain_core.messages import HumanMessage

            # Initialize the model
            model = ClaudeChatModel(
                model_name="claude-opus-4-5",
                project_id="your-gcp-project-id",
                location="global",
                max_tokens=1024
            )

            # --- Text-only usage (automatically traced if env vars set) ---
            response = model.invoke("Hello, how are you?")
            print("Text response:", response.content)

            # --- Tracing with session/user tracking (for Langfuse) ---
            response = model.invoke(
                "What is AI?",
                config={
                    "metadata": {
                        "langfuse_session_id": "chat-session-123",
                        "langfuse_user_id": "user-456"
                    }
                }
            )

            # --- Multi-turn conversation ---
            messages = [
                HumanMessage(content="Hi there!"),
                AIMessage(content="Hello! How can I help you today?"),
                HumanMessage(content="Tell me about yourself.")
            ]
            response = model.invoke(messages)
            print("Conversation response:", response.content)

            # --- Streaming usage ---
            print("Streaming response:")
            for chunk in model.stream("Tell me a short story"):
                print(chunk.content, end="", flush=True)

            # --- With system message ---
            from langchain_core.messages import SystemMessage

            messages = [
                SystemMessage(content="You are a helpful assistant specialized in Python."),
                HumanMessage(content="How do I read a file in Python?")
            ]
            response = model.invoke(messages)
            print(response.content)

            # --- Disable tracing for specific calls ---
            response = model.invoke(
                "Hello without tracing",
                config={"metadata": {"tracing_disabled": True}}
            )

    Note:
        - Before running, authenticate with GCP: `gcloud auth application-default login`
        - Model IDs use the format: "claude-opus-4-5" (the SDK handles version suffixes)
        - The "global" location provides maximum availability with dynamic routing
        - Regional endpoints (e.g., "us-east1") guarantee data routing through specific locations
    """

    # Model configuration
    model_name: str = Field(
        default="claude-sonnet-4-5",
        description="Claude model name (e.g., 'claude-opus-4-5', 'claude-sonnet-4-5')"
    )
    project_id: str = Field(description="Google Cloud Project ID")
    location: str = Field(
        default="global",
        description="Google Cloud location (e.g., 'global', 'us-east1', 'europe-west1')"
    )
    temperature: Optional[float] = Field(default=1.0, description="Sampling temperature (0.0 to 1.0)")
    max_tokens: int = Field(default=4096, description="Maximum tokens to generate")
    top_p: Optional[float] = Field(default=None, description="Top-p sampling parameter")
    top_k: Optional[int] = Field(default=None, description="Top-k sampling parameter")

    # Authentication
    service_account_file: Optional[str] = Field(
        default=None,
        description="Path to Google Cloud service account key file"
    )

    # Configuration for tracing and logging
    logger: Optional[logging.Logger] = Field(default=None, description="Optional logger instance", exclude=True)
    enable_tracing: Optional[bool] = Field(default=None, description="Enable tracing (auto-detect if None)")
    disable_streaming: bool = Field(default=False, description="Disable streaming for this model")

    # Internal clients and managers
    _client: Optional[Any] = None
    _async_client: Optional[Any] = None
    _tracing_manager: Optional[TracingManager] = None
    _bound_tools: Optional[List[Dict[str, Any]]] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialize logger
        if self.logger is None:
            self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
            if not self.logger.handlers:
                self.logger.addHandler(logging.StreamHandler())
                self.logger.setLevel(logging.INFO)

        self._initialize_client()
        self._tracing_manager = TracingManager(self)

    def _initialize_client(self):
        """Initializes the AnthropicVertex client."""
        if not ANTHROPIC_VERTEX_AVAILABLE:
            error_msg = (
                "anthropic[vertex] package is required. "
                "Install with: pip install 'anthropic[vertex]'"
            )
            self.logger.error(error_msg)
            raise ImportError(error_msg)

        # Get project_id from environment if not provided
        if not self.project_id:
            self.project_id = os.getenv("GCP_PROJECT_ID")

        if not self.project_id:
            error_msg = "project_id is required. Set GCP_PROJECT_ID environment variable or pass project_id parameter."
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        # Get location from environment if not provided
        if not self.location:
            self.location = os.getenv("GCP_LOCATION", "global")

        # Set service account file from environment if available
        if not self.service_account_file:
            self.service_account_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        # Set environment variable for google-auth-library if service account file is provided
        if self.service_account_file:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.service_account_file
            self.logger.debug(f"Using service account file: {self.service_account_file}")

        try:
            # Initialize the AnthropicVertex clients (sync and async)
            # The clients use google-auth-library for authentication
            self._client = AnthropicVertex(
                project_id=self.project_id,
                region=self.location
            )

            # Initialize async client for async operations
            self._async_client = AsyncAnthropicVertex(
                project_id=self.project_id,
                region=self.location
            )

            self.logger.info(
                f"Initialized ClaudeChatModel with model: {self.model_name} "
                f"(Project: {self.project_id}, Location: {self.location})"
            )
        except Exception as e:
            error_msg = f"Failed to initialize AnthropicVertex client: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg)

    def get_model_identifier(self) -> str:
        """Return a string identifying this model for tracing and logging."""
        return f"{self.__class__.__name__} (model='{self.model_name}')"

    def _convert_tools_to_claude_format(self, tools: List) -> List[Dict[str, Any]]:
        """
        Converts LangChain tools to Claude's tool format according to the official API specification.

        Claude's tool format requires:
        - name: Tool name matching regex ^[a-zA-Z0-9_-]{1,64}$
        - description: Detailed plaintext description
        - input_schema: JSON Schema object defining expected parameters

        Args:
            tools: List of LangChain tools (BaseTool instances or tool-like objects)

        Returns:
            List of tools in Claude's API format

        Reference: https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use
        """
        claude_tools = []

        for tool in tools:
            # Handle LangChain tool objects
            if hasattr(tool, 'name') and hasattr(tool, 'description'):
                claude_tool = {
                    "name": tool.name,
                    "description": tool.description or ""
                }

                # Extract input_schema from the tool
                if hasattr(tool, 'args_schema') and tool.args_schema:
                    try:
                        # Get JSON schema from Pydantic model
                        schema = tool.args_schema.model_json_schema()
                        claude_tool["input_schema"] = {
                            "type": "object",
                            "properties": schema.get("properties", {}),
                            "required": schema.get("required", [])
                        }
                    except Exception as e:
                        self.logger.warning(f"Failed to extract schema for tool {tool.name}: {e}")
                        claude_tool["input_schema"] = {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                elif hasattr(tool, 'args') and isinstance(tool.args, dict):
                    # Fallback to args dict if available
                    claude_tool["input_schema"] = {
                        "type": "object",
                        "properties": tool.args,
                        "required": []
                    }
                else:
                    # No schema available, use empty schema
                    claude_tool["input_schema"] = {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }

                claude_tools.append(claude_tool)
            elif isinstance(tool, dict):
                # Already a dict, assume it's in Claude format or compatible format
                claude_tools.append(tool)
            else:
                self.logger.warning(f"Unsupported tool type: {type(tool)}")

        return claude_tools

    def bind_tools(
        self,
        tools: List,
        **kwargs: Any,
    ) -> "ClaudeChatModel":
        """
        Bind tools to this model, returning a new Runnable with tools configured.

        This method converts LangChain tools to Claude's API format and uses the parent
        class's bind() method to attach them to the model. The tools parameter will be
        passed to the Claude Messages API as documented in:
        https://platform.claude.com/docs/en/agents-and-tools/tool-use

        Args:
            tools: A sequence of LangChain tools to bind to the model
            **kwargs: Additional keyword arguments (e.g., tool_choice)

        Returns:
            A new Runnable wrapping this model with tools bound. When invoke() or
            astream() is called on the returned Runnable, the tools will automatically
            be included in the API request.

        Example:
            >>> model = ClaudeChatModel(model_name="claude-sonnet-4-5", project_id="my-project")
            >>> tools = [my_search_tool, my_calculator_tool]
            >>> model_with_tools = model.bind_tools(tools)
            >>> # Now invoke() will automatically pass tools to the API
            >>> response = model_with_tools.invoke("What's the weather?")
        """
        # Convert tools to Claude format
        claude_tools = self._convert_tools_to_claude_format(tools) if tools else []

        self.logger.info(f"Binding {len(claude_tools)} tools to model")

        # Use the parent bind() method to create a new RunnableBinding
        # that will inject 'tools' parameter into every invocation
        return super().bind(tools=claude_tools, **kwargs)

    def invoke(self, input, config=None, **kwargs):
        """Override invoke to add tracing callbacks automatically."""
        config = self._tracing_manager.add_sync_callbacks_to_config(config)
        return super().invoke(input, config=config, **kwargs)

    async def ainvoke(self, input, config=None, **kwargs):
        """Override ainvoke to add tracing callbacks automatically."""
        config = self._tracing_manager.add_async_callbacks_to_config(config)
        return await super().ainvoke(input, config=config, **kwargs)

    def stream(self, input, config=None, **kwargs):
        """Override stream to add tracing callbacks automatically."""
        config = self._tracing_manager.add_sync_callbacks_to_config(config)
        return super().stream(input, config=config, **kwargs)

    async def astream(self, input, config=None, **kwargs):
        """Override astream to add tracing callbacks automatically."""
        config = self._tracing_manager.add_async_callbacks_to_config(config)
        async for chunk in super().astream(input, config=config, **kwargs):
            yield chunk

    @property
    def _llm_type(self) -> str:
        """Return identifier for the model type."""
        return "claude_vertex_ai"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Return a dictionary of identifying parameters for tracing."""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "project_id": self.project_id,
            "location": self.location,
        }

    def _convert_messages(self, messages: List[BaseMessage]) -> tuple[Optional[str], List[Dict[str, Any]]]:
        """
        Converts LangChain messages to Claude's message format.

        Handles:
        - SystemMessage -> system parameter
        - HumanMessage -> user role
        - AIMessage -> assistant role (with tool_use blocks if tool_calls present)
        - ToolMessage -> user role with tool_result blocks

        Returns:
            tuple: (system_message, messages_list)
                - system_message: Combined system instructions or None
                - messages_list: List of message dicts with role and content
        """
        self.logger.debug(f"Converting {len(messages)} messages.")

        # Extract system messages
        system_prompts = [
            msg.content for msg in messages
            if isinstance(msg, SystemMessage) and msg.content
        ]
        system_message = "\n\n".join(system_prompts) if system_prompts else None

        # Convert chat messages (filter out system messages)
        chat_messages = [msg for msg in messages if not isinstance(msg, SystemMessage)]

        claude_messages = []
        for msg in chat_messages:
            if isinstance(msg, HumanMessage):
                # User message
                claude_messages.append({
                    "role": "user",
                    "content": msg.content
                })

            elif isinstance(msg, AIMessage):
                # Assistant message - may include tool calls
                content_blocks = []

                # Add text content if present
                if msg.content:
                    if isinstance(msg.content, str):
                        content_blocks.append({
                            "type": "text",
                            "text": msg.content
                        })
                    elif isinstance(msg.content, list):
                        # Already structured content
                        content_blocks.extend(msg.content)

                # Add tool_use blocks if present
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        content_blocks.append({
                            "type": "tool_use",
                            "id": tool_call["id"],
                            "name": tool_call["name"],
                            "input": tool_call["args"]
                        })

                # Only add message if there's content
                if content_blocks:
                    claude_messages.append({
                        "role": "assistant",
                        "content": content_blocks
                    })

            elif isinstance(msg, ToolMessage):
                # Tool result - must be in user role with tool_result content block
                content_blocks = [{
                    "type": "tool_result",
                    "tool_use_id": msg.tool_call_id,
                    "content": msg.content
                }]

                claude_messages.append({
                    "role": "user",
                    "content": content_blocks
                })

            else:
                self.logger.warning(f"Unsupported message type: {type(msg)}")
                continue

        return system_message, claude_messages

    def _prepare_request_params(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Prepares the request parameters for Claude API."""
        system_message, claude_messages = self._convert_messages(messages)

        # Build request parameters
        params = {
            "model": self.model_name,
            "max_tokens": self.max_tokens,
            "messages": claude_messages,
        }

        # Add optional parameters
        if system_message:
            params["system"] = system_message

        if self.temperature is not None:
            params["temperature"] = self.temperature

        if self.top_p is not None:
            params["top_p"] = self.top_p

        if self.top_k is not None:
            params["top_k"] = self.top_k

        if stop:
            params["stop_sequences"] = stop

        # Add tools if provided (from bind_tools)
        if "tools" in kwargs and kwargs["tools"]:
            params["tools"] = kwargs["tools"]

        # Add tool_choice if provided
        if "tool_choice" in kwargs:
            params["tool_choice"] = kwargs["tool_choice"]

        return params

    def _map_usage_metadata(self, usage: Any) -> Optional[Dict]:
        """Maps Claude's usage metadata to LangChain's expected format."""
        if not usage:
            return None

        return {
            "input_tokens": getattr(usage, "input_tokens", 0),
            "output_tokens": getattr(usage, "output_tokens", 0),
            "total_tokens": getattr(usage, "input_tokens", 0) + getattr(usage, "output_tokens", 0),
        }

    def _create_chat_result_with_usage(self, response) -> ChatResult:
        """
        Creates a ChatResult with usage metadata for tracing.

        Handles both text and tool_use content blocks from Claude's API.
        """
        # Extract text content and tool calls from response
        content_text = ""
        tool_calls = []

        if hasattr(response, "content") and response.content:
            # Handle different content block types
            for block in response.content:
                # Text block
                if hasattr(block, "text"):
                    content_text += block.text
                # Tool use block
                elif hasattr(block, "type") and block.type == "tool_use":
                    tool_call = {
                        "name": block.name,
                        "args": block.input,
                        "id": block.id
                    }
                    tool_calls.append(tool_call)

        # Get stop reason
        stop_reason = getattr(response, "stop_reason", None)

        # Map usage metadata
        usage_dict = self._map_usage_metadata(getattr(response, "usage", None)) or {}

        # Build AIMessage with tool calls if present
        message_kwargs = {
            "content": content_text,
            "response_metadata": {
                "model": getattr(response, "model", self.model_name),
                "stop_reason": stop_reason,
                **usage_dict
            }
        }

        # Add tool_calls if any were found
        if tool_calls:
            message_kwargs["tool_calls"] = tool_calls

        message = AIMessage(**message_kwargs)

        generation = ChatGeneration(
            message=message,
            generation_info={"token_usage": usage_dict} if usage_dict else None
        )

        chat_result = ChatResult(
            generations=[generation],
            llm_output={
                "token_usage": usage_dict,
                "model_name": self.model_name
            } if usage_dict else {
                "model_name": self.model_name
            }
        )

        return chat_result

    def _create_chat_generation_chunk(self, delta_text: str) -> ChatGenerationChunk:
        """Creates a ChatGenerationChunk for streaming."""
        return ChatGenerationChunk(
            message=AIMessageChunk(
                content=delta_text,
                response_metadata={"model_name": self.model_name},
            ),
            generation_info=None,
        )

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generates a chat response from a list of messages."""
        self.logger.info(f"Generating response for {len(messages)} messages.")

        params = self._prepare_request_params(messages, stop, **kwargs)

        try:
            response = self._client.messages.create(**params)
            return self._create_chat_result_with_usage(response)

        except Exception as e:
            self.logger.error(f"Error generating content with Claude: {e}", exc_info=True)
            raise ValueError(f"Error during generation: {e}")

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Asynchronously generates a chat response."""
        self.logger.info(f"Async generating response for {len(messages)} messages.")

        params = self._prepare_request_params(messages, stop, **kwargs)

        try:
            response = await self._async_client.messages.create(**params)
            return self._create_chat_result_with_usage(response)

        except Exception as e:
            self.logger.error(f"Error during async generation: {e}", exc_info=True)
            raise ValueError(f"Error during async generation: {e}")

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """Streams the chat response."""
        self.logger.info(f"Streaming response for {len(messages)} messages.")

        params = self._prepare_request_params(messages, stop, **kwargs)

        try:
            final_usage_metadata = None

            with self._client.messages.stream(**params) as stream:
                for text in stream.text_stream:
                    if text:
                        yield self._create_chat_generation_chunk(text)

                # Get final message with usage info
                final_message = stream.get_final_message()
                if hasattr(final_message, "usage"):
                    final_usage_metadata = final_message.usage

            # Yield final chunk with usage metadata
            if final_usage_metadata:
                usage_dict = self._map_usage_metadata(final_usage_metadata)
                if usage_dict:
                    yield ChatGenerationChunk(
                        message=AIMessageChunk(content="", usage_metadata=usage_dict)
                    )

        except Exception as e:
            self.logger.error(f"Error streaming content: {e}", exc_info=True)
            raise ValueError(f"Error during streaming: {e}")

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        """Asynchronously streams the chat response."""
        self.logger.info(f"Async streaming response for {len(messages)} messages.")

        params = self._prepare_request_params(messages, stop, **kwargs)

        try:
            final_usage_metadata = None

            async with self._async_client.messages.stream(**params) as stream:
                async for text in stream.text_stream:
                    if text:
                        yield self._create_chat_generation_chunk(text)

                # Get final message with usage info
                final_message = await stream.get_final_message()
                if hasattr(final_message, "usage"):
                    final_usage_metadata = final_message.usage

            # Yield final chunk with usage metadata
            if final_usage_metadata:
                usage_dict = self._map_usage_metadata(final_usage_metadata)
                if usage_dict:
                    yield ChatGenerationChunk(
                        message=AIMessageChunk(content="", usage_metadata=usage_dict)
                    )

        except Exception as e:
            self.logger.error(f"Error during async streaming: {e}", exc_info=True)
            raise ValueError(f"Error during async streaming: {e}")
