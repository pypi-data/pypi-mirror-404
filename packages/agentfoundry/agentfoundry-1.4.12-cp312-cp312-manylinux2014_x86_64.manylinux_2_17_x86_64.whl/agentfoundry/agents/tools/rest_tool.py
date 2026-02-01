import base64
import json
import logging

logging.getLogger("requests.packages.urllib3").setLevel(logging.DEBUG)
logging.getLogger("requests.packages.urllib3").propagate = True

import requests
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Define a structured input model for the REST API call.
class RestApiInput(BaseModel):
    method: str = Field(..., description="HTTP(S) method (e.g., GET, POST)")
    url: str = Field(..., description="The API endpoint URL")
    verify_ssl: bool = Field(False, description="Flag to verify SSL certificates (default: True)")
    headers: dict = Field(default_factory=dict, description="Optional HTTP headers")
    params: dict = Field(default_factory=dict, description="Optional URL parameters")
    body: dict = Field(default_factory=dict, description="Optional JSON body for the request")


def rest_tool(method: str, url: str, verify_ssl: bool = False, headers: dict = {}, params: dict = {}, body: dict = {}) -> dict:
    """
    Executes a REST API call with the specified parameters, supporting various HTTP methods and data sources.

    Args:
        method: HTTP method (e.g., GET, POST).
        url: The API endpoint URL.
        headers: Optional headers (e.g., for authentication or content type).
        params: Optional query parameters.
        body: Optional JSON body for POST/PUT requests.
        verify_ssl: Whether to verify SSL certificates (True by default; False disables verification, reducing security).

    Returns:
        dict: The JSON response from the API if the content type is 'application/json',
              a dict with the text response under 'response' if not JSON,
              or an error message under 'error' if the call fails.

    Example:
        To query an API:
        {
            "method": "GET",
            "url": "https://api.example.com/data",
            "headers": {"Authorization": "Basic <base64_encoded_credentials>"},
            "params": {"limit": 10},
            "verify_ssl": False
        }
    """
    logger.info(f"Calling REST API with received input: {input}")
    print(f"Calling REST API with received input: {input}")
    try:
        response = requests.request(
            method=method if method else "GET",
            url=url,
            headers=headers if headers else None,
            params=params if params else None,
            json=body if body else None,
            timeout=20,
            verify=verify_ssl
        )

        logger.info(f"REST API call to {url} returned status: {response.status_code}")
        content_type = response.headers.get("Content-Type", "")
        return response.json() if response.ok else {"error": response.text}

    except Exception as e:
        logger.error(f"Error calling REST API: {str(e)}", exc_info=True)
        return {"error": f"REST API call failed: {str(e)}"}


# Wrap the function as a LangChain Tool.
rest_api_tool = StructuredTool.from_function(
    func=rest_tool,
    name="rest_api_tool",
    description=rest_tool.__doc__,
    args_schema=RestApiInput  # Always add the args_schema to the tool definition for better validation and documentation.
)


# Example usage:
if __name__ == "__main__":
    # Prepare an example input as a dictionary.
    example_input = {
        "method": "GET",
        "url": "https://api.apis.guru/v2/list.json",
        "params": {},
        "body": {},
        "verify_ssl": False
    }

    # Invoke the tool with the dictionary input.
    result = rest_api_tool.invoke(example_input)
    print("REST API Tool result:", json.dumps(result, indent=2))
