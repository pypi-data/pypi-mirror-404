"""
Tests for GeminiChatModel's bind_tools functionality.

This test suite validates the tool binding feature for Gemini models,
including tool conversion, binding, and invocation.

Langfuse tracing is enabled for integration tests to track performance and usage.
"""

import os
import sys
from pathlib import Path
import pytest
from typing import Optional
from pydantic import BaseModel, Field
from google.genai import types
from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from crewplus.services import init_load_balancer, get_model_balancer


# =============================================================================
# Test Tools Definition
# =============================================================================

class CalculatorInput(BaseModel):
    """Input schema for calculator tool."""
    operation: str = Field(
        description="The operation to perform: 'add', 'subtract', 'multiply', or 'divide'"
    )
    a: float = Field(description="The first number")
    b: float = Field(description="The second number")


class CalculatorTool(BaseTool):
    """A simple calculator tool for basic arithmetic operations."""

    name: str = "calculator"
    description: str = (
        "Performs basic arithmetic operations (add, subtract, multiply, divide). "
        "Use this tool when you need to calculate numerical results. "
        "Provide the operation type and two numbers."
    )
    args_schema: type[BaseModel] = CalculatorInput

    def _run(self, operation: str, a: float, b: float) -> str:
        """Execute the calculator operation."""
        try:
            if operation == "add":
                result = a + b
                return f"The result of {a} + {b} is {result}"
            elif operation == "subtract":
                result = a - b
                return f"The result of {a} - {b} is {result}"
            elif operation == "multiply":
                result = a * b
                return f"The result of {a} × {b} is {result}"
            elif operation == "divide":
                if b == 0:
                    return "Error: Cannot divide by zero"
                result = a / b
                return f"The result of {a} ÷ {b} is {result}"
            else:
                return f"Error: Unknown operation '{operation}'"
        except Exception as e:
            return f"Error performing calculation: {str(e)}"

    async def _arun(self, operation: str, a: float, b: float) -> str:
        """Async version of _run."""
        return self._run(operation, a, b)


class WeatherInput(BaseModel):
    """Input schema for weather tool."""
    location: str = Field(description="The city or location to get weather for")
    unit: str = Field(default="celsius", description="Temperature unit: 'celsius' or 'fahrenheit'")


class WeatherTool(BaseTool):
    """A mock weather tool."""

    name: str = "get_weather"
    description: str = (
        "Gets the current weather for a given location. "
        "Returns temperature and conditions."
    )
    args_schema: type[BaseModel] = WeatherInput

    def _run(self, location: str, unit: str = "celsius") -> str:
        """Execute the weather lookup."""
        # Mock response
        temp = 22 if unit == "celsius" else 72
        return f"The weather in {location} is sunny with a temperature of {temp}°{unit[0].upper()}."

    async def _arun(self, location: str, unit: str = "celsius") -> str:
        """Async version of _run."""
        return self._run(location, unit)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="module")
def langfuse_config():
    """Configure Langfuse environment variables for tracing."""
    # Set Langfuse configuration
    os.environ["LANGFUSE_PUBLIC_KEY"] = os.getenv(
        "LANGFUSE_PUBLIC_KEY",
        "pk-lf-874857f5-6bad-4141-96eb-cf36f70009e6"
    )
    os.environ["LANGFUSE_SECRET_KEY"] = os.getenv(
        "LANGFUSE_SECRET_KEY",
        "sk-lf-3fe02b88-be46-4394-8da0-9ec409660de1"
    )
    os.environ["LANGFUSE_HOST"] = os.getenv(
        "LANGFUSE_HOST",
        "https://langfuse-test.crewplus.ai"
    )

    yield {
        "public_key": os.environ["LANGFUSE_PUBLIC_KEY"],
        "secret_key": os.environ["LANGFUSE_SECRET_KEY"],
        "host": os.environ["LANGFUSE_HOST"]
    }


@pytest.fixture(scope="module")
def model_balancer(langfuse_config):
    """Initialize and return the model load balancer."""
    config_path = PROJECT_ROOT / "_config" / "models_config.json"
    if not config_path.exists():
        pytest.skip(f"Config file not found: {config_path}")

    init_load_balancer(str(config_path))
    return get_model_balancer()


@pytest.fixture(params=[
    # "gemini-2.5-flash",  # Google AI
    "gemini-2.5-flash@us-central1",  # Vertex AI
])
def gemini_model(request, model_balancer):
    """Create a GeminiChatModel instance from model balancer for testing."""
    deployment_name = request.param

    try:
        model = model_balancer.get_model(deployment_name=deployment_name)

        # Enable tracing for integration tests, disable for unit tests
        # Integration tests are marked with @pytest.mark.integration
        if hasattr(model, 'enable_tracing'):
            # Check if we're in an integration test
            if hasattr(request, 'node') and request.node.get_closest_marker('integration'):
                model.enable_tracing = True
            else:
                model.enable_tracing = False

        return model
    except Exception as e:
        pytest.skip(f"Could not get model '{deployment_name}': {e}")


@pytest.fixture
def calculator_tool():
    """Create a calculator tool instance."""
    return CalculatorTool()


@pytest.fixture
def weather_tool():
    """Create a weather tool instance."""
    return WeatherTool()


# =============================================================================
# Test Tool Conversion
# =============================================================================

class TestToolConversion:
    """Tests for the _convert_langchain_tool_to_gemini_declaration method."""

    def test_convert_calculator_tool_to_declaration(self, gemini_model, calculator_tool):
        """Test converting a LangChain tool to Gemini FunctionDeclaration."""
        func_decl = gemini_model._convert_langchain_tool_to_gemini_declaration(calculator_tool)

        assert func_decl is not None
        assert isinstance(func_decl, types.FunctionDeclaration)
        assert func_decl.name == "calculator"
        assert "arithmetic" in func_decl.description.lower()

        # Check parameters schema
        assert func_decl.parameters.type == types.Type.OBJECT
        assert "operation" in func_decl.parameters.properties
        assert "a" in func_decl.parameters.properties
        assert "b" in func_decl.parameters.properties
        assert set(func_decl.parameters.required) == {"operation", "a", "b"}

    def test_convert_weather_tool_to_declaration(self, gemini_model, weather_tool):
        """Test converting a weather tool to Gemini FunctionDeclaration."""
        func_decl = gemini_model._convert_langchain_tool_to_gemini_declaration(weather_tool)

        assert func_decl is not None
        assert isinstance(func_decl, types.FunctionDeclaration)
        assert func_decl.name == "get_weather"
        assert "weather" in func_decl.description.lower()

        # Check parameters
        assert "location" in func_decl.parameters.properties
        assert "unit" in func_decl.parameters.properties
        # Only location is required, unit has a default
        assert "location" in func_decl.parameters.required

    def test_convert_invalid_tool(self, gemini_model):
        """Test that invalid tools return None."""
        # Tool without name
        class InvalidTool:
            description = "Test"

        result = gemini_model._convert_langchain_tool_to_gemini_declaration(InvalidTool())
        assert result is None

    def test_type_mapping(self, gemini_model, calculator_tool):
        """Test that JSON schema types are correctly mapped to Gemini types."""
        func_decl = gemini_model._convert_langchain_tool_to_gemini_declaration(calculator_tool)

        # operation should be STRING type
        assert func_decl.parameters.properties["operation"].type == types.Type.STRING

        # a and b should be NUMBER type (float in Pydantic)
        assert func_decl.parameters.properties["a"].type == types.Type.NUMBER
        assert func_decl.parameters.properties["b"].type == types.Type.NUMBER


# =============================================================================
# Test bind_tools Method
# =============================================================================

class TestBindTools:
    """Tests for the bind_tools method."""

    def test_bind_single_tool(self, gemini_model, calculator_tool):
        """Test binding a single tool to the model."""
        model_with_tools = gemini_model.bind_tools([calculator_tool])

        # Should return a RunnableBinding
        assert model_with_tools is not None
        assert hasattr(model_with_tools, "invoke")

        # Check that tools were bound (they're in kwargs)
        assert hasattr(model_with_tools, "kwargs")
        assert "tools" in model_with_tools.kwargs
        assert len(model_with_tools.kwargs["tools"]) == 1
        assert isinstance(model_with_tools.kwargs["tools"][0], types.FunctionDeclaration)

    def test_bind_multiple_tools(self, gemini_model, calculator_tool, weather_tool):
        """Test binding multiple tools to the model."""
        model_with_tools = gemini_model.bind_tools([calculator_tool, weather_tool])

        # Check that both tools were bound
        assert len(model_with_tools.kwargs["tools"]) == 2

        # Check tool names
        tool_names = {t.name for t in model_with_tools.kwargs["tools"]}
        assert tool_names == {"calculator", "get_weather"}

    def test_bind_empty_list(self, gemini_model):
        """Test binding an empty list of tools."""
        model_with_tools = gemini_model.bind_tools([])

        # Should still work, just with no tools
        assert "tools" in model_with_tools.kwargs
        assert model_with_tools.kwargs["tools"] == []

    def test_bind_with_additional_kwargs(self, gemini_model, calculator_tool):
        """Test binding tools with additional kwargs."""
        model_with_tools = gemini_model.bind_tools(
            [calculator_tool],
            tool_config={"function_calling_config": {"mode": "AUTO"}}
        )

        # Tools should be bound
        assert len(model_with_tools.kwargs["tools"]) == 1

        # Additional kwargs should also be present
        assert "tool_config" in model_with_tools.kwargs


# =============================================================================
# Test Integration with Model Invocation
# =============================================================================

@pytest.mark.integration
class TestToolInvocation:
    """Tests for actual tool invocation with the model."""

    def test_simple_calculation_with_tools(self, gemini_model, calculator_tool):
        """Test a simple calculation using the bound tool."""
        model_with_tools = gemini_model.bind_tools([calculator_tool])

        query = "What is 15 + 27?"
        response = model_with_tools.invoke(query)

        # Check response
        assert response is not None
        assert isinstance(response, AIMessage)

        # The model should either:
        # 1. Use the tool (have tool_calls)
        # 2. Answer directly with knowledge
        # We'll just check it responded
        assert response.content is not None or (
            hasattr(response, 'tool_calls') and response.tool_calls
        )

    def test_tool_calls_structure(self, gemini_model, calculator_tool):
        """Test that tool calls have the correct structure."""
        model_with_tools = gemini_model.bind_tools([calculator_tool])

        query = "Calculate 8 times 7 using the calculator"
        response = model_with_tools.invoke(query)

        # If tool was called, check structure
        if hasattr(response, 'tool_calls') and response.tool_calls:
            tool_call = response.tool_calls[0]

            assert 'name' in tool_call
            assert 'args' in tool_call
            assert 'id' in tool_call

            # Check args structure for calculator
            args = tool_call['args']
            if 'operation' in args:  # If tool was called
                assert args['operation'] in ['add', 'subtract', 'multiply', 'divide']
                assert 'a' in args
                assert 'b' in args

    def test_complete_tool_execution_loop(self, gemini_model, calculator_tool):
        """Test a complete tool execution loop: request -> tool call -> execution -> final answer."""
        model_with_tools = gemini_model.bind_tools([calculator_tool])

        # Step 1: Initial query
        query = "What is 15 + 27?"
        response = model_with_tools.invoke(query)

        print(f"\nStep 1: Initial Response")
        print(f"  Content: {response.content}")
        if hasattr(response, 'tool_calls'):
            print(f"  Tool Calls: {response.tool_calls}")

        # Step 2: Execute tools and build message history
        if hasattr(response, 'tool_calls') and response.tool_calls:
            messages = [
                HumanMessage(content=query),
                response  # The AIMessage with tool_calls
            ]

            # Execute each tool call
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_id = tool_call["id"]

                print(f"\nStep 2: Executing tool '{tool_name}'")
                print(f"  Arguments: {tool_args}")

                # Execute the tool
                if tool_name == "calculator":
                    tool_result = calculator_tool._run(**tool_args)
                    print(f"  Result: {tool_result}")

                    # Add tool result as a ToolMessage
                    messages.append(
                        ToolMessage(
                            content=tool_result,
                            tool_call_id=tool_id
                        )
                    )

            # Step 3: Get final response
            print("\nStep 3: Getting final response...")
            final_response = model_with_tools.invoke(messages)

            print(f"\nFinal Answer: {final_response.content}")

            assert final_response is not None
            assert final_response.content is not None
            # The final answer should mention the result (42)
            assert "42" in final_response.content

    def test_multiple_tools_selection(self, gemini_model, calculator_tool, weather_tool):
        """Test that the model can choose between multiple tools."""
        model_with_tools = gemini_model.bind_tools([calculator_tool, weather_tool])

        # Ask a weather question
        query = "What's the weather like in Tokyo?"
        response = model_with_tools.invoke(query)

        assert response is not None

        # If tool was called, it should be the weather tool
        if hasattr(response, 'tool_calls') and response.tool_calls:
            assert any(tc['name'] == 'get_weather' for tc in response.tool_calls)


# =============================================================================
# Test Backward Compatibility
# =============================================================================

class TestBackwardCompatibility:
    """Tests to ensure backward compatibility."""

    def test_model_without_tools_still_works(self, gemini_model):
        """Test that the model still works without binding tools."""
        # This should work exactly as before
        query = "Hello! How are you?"
        response = gemini_model.invoke(query)

        assert response is not None
        assert isinstance(response, AIMessage)
        assert response.content is not None

    def test_prepare_generation_config_without_tools(self, gemini_model):
        """Test that _prepare_generation_config works without tools."""
        messages = [HumanMessage(content="Test")]
        config = gemini_model._prepare_generation_config(messages, stop=None, tools=None)

        assert isinstance(config, types.GenerateContentConfig)
        assert not hasattr(config, 'tools') or config.tools is None

    def test_prepare_generation_config_with_tools(self, gemini_model, calculator_tool):
        """Test that _prepare_generation_config works with tools."""
        messages = [HumanMessage(content="Test")]
        func_decl = gemini_model._convert_langchain_tool_to_gemini_declaration(calculator_tool)

        config = gemini_model._prepare_generation_config(
            messages,
            stop=None,
            tools=[func_decl]
        )

        assert isinstance(config, types.GenerateContentConfig)
        assert config.tools is not None
        assert len(config.tools) == 1
        assert isinstance(config.tools[0], types.Tool)
        # Check that the tool contains our function declaration
        assert len(config.tools[0].function_declarations) == 1
        assert config.tools[0].function_declarations[0].name == "calculator"


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_rebinding_tools(self, gemini_model, calculator_tool, weather_tool):
        """Test binding tools multiple times."""
        # First binding
        model_with_calc = gemini_model.bind_tools([calculator_tool])
        assert len(model_with_calc.kwargs["tools"]) == 1

        # Second binding (should replace, not append)
        model_with_weather = model_with_calc.bind_tools([weather_tool])
        assert len(model_with_weather.kwargs["tools"]) == 1
        assert model_with_weather.kwargs["tools"][0].name == "get_weather"

    @pytest.mark.integration
    def test_streaming_with_tools(self, gemini_model, calculator_tool):
        """Test that streaming works with bound tools."""
        model_with_tools = gemini_model.bind_tools([calculator_tool])

        query = "What is 5 + 3?"
        chunks = list(model_with_tools.stream(query))

        # Should receive chunks
        assert len(chunks) > 0

        # At least one chunk should have content or tool calls
        assert any(
            chunk.content or (hasattr(chunk, 'tool_calls') and chunk.tool_calls)
            for chunk in chunks
        )


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    # Run with: python test_gemini_bind_tools.py
    # Or: pytest test_gemini_bind_tools.py -v
    pytest.main([__file__, "-v", "--tb=short", "-m", "not integration"])
