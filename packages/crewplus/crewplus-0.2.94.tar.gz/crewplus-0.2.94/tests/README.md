# CrewPlus Tests

This directory contains tests for the crewplus-base package, with full Langfuse tracing support.

## Test Structure

- `test_gemini_bind_tools.py` - Tests for GeminiChatModel's bind_tools functionality
  - Tool conversion tests
  - Tool binding tests
  - Integration tests with actual API calls
  - Backward compatibility tests
  - Edge case tests

## Running Tests

### Prerequisites

1. Install test dependencies:
```bash
pip install pytest
```

2. Ensure the config file exists:
```bash
# Config file should be at: ../_config/models_config.json
```

3. Environment variables (optional - defaults are provided):
```bash
# Langfuse tracing (automatically configured with defaults)
export LANGFUSE_PUBLIC_KEY="your-public-key"
export LANGFUSE_SECRET_KEY="your-secret-key"
export LANGFUSE_HOST="your-langfuse-host"
```

### Run All Tests

```bash
# From the tests directory
pytest test_gemini_bind_tools.py -v

# Or from the package root
pytest tests/ -v
```

### Run Specific Test Classes

```bash
# Test only tool conversion
pytest test_gemini_bind_tools.py::TestToolConversion -v

# Test only bind_tools method
pytest test_gemini_bind_tools.py::TestBindTools -v

# Test only backward compatibility
pytest test_gemini_bind_tools.py::TestBackwardCompatibility -v
```

### Run Without Integration Tests

Integration tests make actual API calls and may incur costs. To skip them:

```bash
pytest test_gemini_bind_tools.py -v -m "not integration"
```

### Run Only Integration Tests

```bash
pytest test_gemini_bind_tools.py -v -m integration
```

### Verbose Output with Full Traceback

```bash
pytest test_gemini_bind_tools.py -vv --tb=long
```

## Langfuse Tracing

Langfuse tracing is automatically enabled for all tests that use the `model_balancer` fixture.

### Default Configuration

The tests use the following default Langfuse configuration:
- **Public Key**: `pk-lf-874857f5-6bad-4141-96eb-cf36f70009e6`
- **Secret Key**: `sk-lf-3fe02b88-be46-4394-8da0-9ec409660de1`
- **Host**: `https://langfuse-test.crewplus.ai`

You can override these by setting environment variables before running tests.

### Viewing Traces

1. Go to your Langfuse dashboard: https://langfuse-test.crewplus.ai
2. Filter by test name or model name to find specific test runs
3. All integration tests (marked with `@pytest.mark.integration`) will have tracing enabled

### Disabling Tracing

Unit tests (without `@pytest.mark.integration`) automatically have tracing disabled for faster execution.

## Test Coverage

The test suite covers:

1. **Tool Conversion** (`TestToolConversion`)
   - Converting LangChain tools to Gemini FunctionDeclarations
   - Type mapping (string, number, boolean, etc.)
   - Handling invalid tools
   - Parameter schema extraction

2. **Tool Binding** (`TestBindTools`)
   - Binding single and multiple tools
   - Empty tool lists
   - Additional kwargs handling

3. **Tool Invocation** (`TestToolInvocation`) - Integration Tests
   - Simple calculations with tools
   - Tool call structure validation
   - Complete tool execution loop
   - Multiple tool selection

4. **Backward Compatibility** (`TestBackwardCompatibility`)
   - Model works without tools
   - Generation config without tools
   - Generation config with tools

5. **Edge Cases** (`TestEdgeCases`)
   - Rebinding tools
   - Streaming with tools

## Test Fixtures

- `langfuse_config` - Sets up Langfuse environment variables (module-scoped)
- `model_balancer` - Initialized model load balancer (module-scoped)
- `gemini_model` - GeminiChatModel instance from balancer (parameterized for both Google AI and Vertex AI)
- `calculator_tool` - Sample calculator tool for testing
- `weather_tool` - Sample weather tool for testing

## Parameterized Tests

The `gemini_model` fixture is parameterized to test both:
- **Google AI**: `gemini-2.5-flash`
- **Vertex AI**: `gemini-2.5-flash@us-central1`

This ensures the bind_tools feature works for both deployment types.

## Bug Fixes

### Vertex AI Tool Binding Fix

The initial implementation had a bug where Vertex AI would fail with:
```
400 INVALID_ARGUMENT: tools[0].tool_type: required one_of 'tool_type' must have one initialized field
```

**Root Cause**: FunctionDeclarations were being passed directly in the config dict, causing them to serialize as empty objects `{}`.

**Fix**:
1. Changed `_prepare_generation_config` to return `types.GenerateContentConfig` object instead of dict
2. Wrapped FunctionDeclarations in `types.Tool(function_declarations=[...])` before adding to config

This ensures proper serialization for both Google AI and Vertex AI endpoints.

## Notes

- Tests use the same `models_config.json` as production code
- Integration tests are marked and can be skipped to avoid API costs
- Tracing is automatically enabled for integration tests
- All test output includes Langfuse trace information when applicable
