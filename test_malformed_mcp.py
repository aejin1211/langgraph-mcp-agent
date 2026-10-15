from mcp.types import CallToolResult
from pydantic import ValidationError


def test_malformed_mcp_response():
    # MCP content must be a list of content blocks, not a string.
    invalid_response = {"content": "not a list", "isError": False}

    try:
        CallToolResult.model_validate(invalid_response)
    except ValidationError as error:
        print("PASS: Malformed MCP response raised ValidationError.")
        print(error)
    else:
        raise AssertionError("Expected ValidationError for malformed MCP content.")


if __name__ == "__main__":
    test_malformed_mcp_response()
