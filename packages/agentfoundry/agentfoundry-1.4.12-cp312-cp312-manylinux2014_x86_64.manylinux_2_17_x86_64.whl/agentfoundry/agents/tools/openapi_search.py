from langchain_core.tools import Tool
from typing import Callable, Dict, Any
from openai import OpenAI


def search_query(query: str) -> str:
    try:
        client = OpenAI()
        response = client.responses.create(
            model="gpt-4.1",
            tools=[{"type": "web_search_preview"}],
            input=query
        )
        return response.output_text
    except Exception as err:
        return f"Error: {str(err)}"


openai_search_tool = Tool(
    name="web_search_tool",
    func=search_query,
    description=(
        "Invokes a websearch using OpenAI's framework. The function takes in a single string input and returns a "
        "string with the result."
    )
)
