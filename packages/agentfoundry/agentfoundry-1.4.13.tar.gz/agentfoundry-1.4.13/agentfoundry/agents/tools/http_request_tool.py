from __future__ import annotations

from typing import Dict, Optional
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
import requests

import logging

logger = logging.getLogger(__name__)


# Define a structured input model for the HTTPRequest tool
class HTTPRequestInput(BaseModel):
    url: str = Field(..., description="The URL to send the HTTP request to (e.g., 'https://api.example.com/data').")
    method: str = Field("GET", description="The HTTP method to use (e.g., 'GET', 'POST', 'PUT', 'DELETE'). Defaults to 'GET'.")
    headers: Optional[Dict[str, str]] = Field(None, description="Optional dictionary of HTTP headers (e.g., {'Authorization': 'Bearer token'}).")
    payload: Optional[Dict] = Field(None, description="Optional dictionary of data to send in the request body (for POST/PUT).")
    timeout: int = Field(10, description="Request timeout in seconds (default: 10).")


def make_http_request(
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        payload: Optional[Dict] = None,
        timeout: int = 10
) -> Dict:
    """
    Performs an HTTP request to the specified URL with the given method, headers, and payload.

    Args:
        url (str): The URL to send the HTTP request to (e.g., 'https://api.example.com/data').
        method (str, optional): The HTTP method to use (e.g., 'GET', 'POST', 'PUT', 'DELETE'). Defaults to 'GET'.
        headers (Dict[str, str], optional): Optional dictionary of HTTP headers (e.g., {'Authorization': 'Bearer token'}).
        payload (Dict, optional): Optional dictionary of data to send in the request body (for POST/PUT).
        timeout (int, optional): Request timeout in seconds (default: 10).

    Returns:
        Dict: A dictionary containing:
            - 'status_code': The HTTP status code (e.g., 200).
            - 'content': The response content (text or JSON if applicable).
            - 'headers': The response headers.
            - 'error': An error message if the request failed (null if successful).

    Example:
        result = make_http_request(
            url="https://api.example.com/data",
            method="GET",
            headers={"Accept": "application/json"},
            timeout=5
        )
        # Returns: {'status_code': 200, 'content': '{"data": "example"}', 'headers': {...}, 'error': null}
    """
    logger.info(f"Making HTTP {method} request to {url} with timeout {timeout}s")
    try:
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=headers,
            json=payload if payload else None,
            timeout=timeout
        )
        # Try to parse JSON content, fall back to text if not JSON
        try:
            content = response.json()
        except ValueError:
            content = response.text
        result = {
            "status_code": response.status_code,
            "content": content,
            "headers": dict(response.headers),
            "error": None
        }
        logger.info(f"HTTP request successful: status {response.status_code}")
        return result
    except Exception as ex:
        logger.error(f"Error during HTTP request to {url}: {ex}")
        return {
            "status_code": None,
            "content": None,
            "headers": None,
            "error": str(ex)
        }


# Wrap as a LangChain tool
http_request_tool = StructuredTool.from_function(
    func=make_http_request,
    name="http_request_tool",
    description=make_http_request.__doc__,
    args_schema=HTTPRequestInput
)

if __name__ == "__main__":
    # Smoke test
    test_input = HTTPRequestInput(
        # url="https://jsonplaceholder.typicode.com/todos/1",
        url="https://www.google.com",
        method="GET",
        headers={"Accept": "application/json"},
        timeout=5,
        payload=None
    )
    print(f"make_http_request description: {make_http_request.__doc__}")
    result = make_http_request(
        url=test_input.url,
        method=test_input.method,
        headers=test_input.headers,
        timeout=test_input.timeout
    )
    print(f"Smoke test result: {result}")
    # Basic validation
    assert "status_code" in result, "Result should contain 'status_code' key"
    assert "content" in result, "Result should contain 'content' key"
    assert "headers" in result, "Result should contain 'headers' key"
    assert "error" in result, "Result should contain 'error' key"
    assert result["status_code"] == 200, "Expected status code 200"
    assert result["error"] is None, "Expected no error"
    assert isinstance(result["content"], dict), "Content should be a JSON dict"
    print("Smoke test passed!")
