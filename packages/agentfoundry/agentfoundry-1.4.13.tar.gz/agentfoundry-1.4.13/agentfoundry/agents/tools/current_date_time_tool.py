from __future__ import annotations

import datetime
from typing import Dict
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
import pytz

import logging

logger = logging.getLogger(__name__)


# Define a structured input model for the CurrentDateTime tool
class DateTimeInput(BaseModel):
    format: str = Field(
        "%Y-%m-%d %H:%M:%S",
        description="The format for the date and time string (default: '%Y-%m-%d %H:%M:%S')."
    )


def get_current_date_time(format: str = "%Y-%m-%d %H:%M:%S", timezone: str = "UTC") -> Dict:
    """
    Retrieves the current date and time, formatted according to the specified format and the specified timezone

    Args:
        format (str, optional): The format for the date and time string, using Python's strftime directives
                               (e.g., '%Y-%m-%d %H:%M:%S' for '2025-05-08 14:30:45'). Defaults to '%Y-%m-%d %H:%M:%S'.
        timezone (str, optional): The timezone to use for the current date and time. Defaults to 'UTC'.

    Returns:
        Dict: A dictionary containing:
            - 'datetime': The formatted date and time string.
            - 'timestamp': The Unix timestamp (seconds since epoch).

    Example:
        result = get_current_date_time(format="%Y-%m-%d %H:%M:%S", timezone="America/New_York")
        Returns: {'datetime': '2025-05-08 14:30:45', 'timestamp': 1741522245.0}
    """
    logger.info(f"Retrieving current date and time with format: {format} {timezone}")
    try:
        # Convert timezone string to timezone object
        timezone = pytz.timezone(timezone)
        current_time = datetime.datetime.now(timezone)
        formatted_time = current_time.strftime(format)
        timestamp = current_time.timestamp()
        result = {"datetime": formatted_time, "timestamp": timestamp}
        logger.info(f"Current date and time: {result}")
        return result
    except Exception as ex:
        logger.error(f"Error retrieving current date and time: {ex}")
        raise ex


# Wrap as a LangChain tool
current_date_time_tool = StructuredTool.from_function(
    func=get_current_date_time,
    name="current_date_time_tool",
    description=get_current_date_time.__doc__,
    args_schema=DateTimeInput
)

if __name__ == "__main__":
    # Smoke test
    test_input = DateTimeInput(format="%Y-%m-%d %H:%M:%S")
    print(f"get_current_date_time description: {get_current_date_time.__doc__}")
    result = get_current_date_time(test_input.format)
    print(f"Current date and time with no timezone specified: {result}")
    result = get_current_date_time(test_input.format,  "America/New_York")
    print(f"Current date and time for America/New_York: {result}")
    # Basic validation
    assert "datetime" in result, "Result should contain 'datetime' key"
    assert "timestamp" in result, "Result should contain 'timestamp' key"
    assert isinstance(result["datetime"], str), "Datetime should be a string"
    assert isinstance(result["timestamp"], float), "Timestamp should be a float"
    print("Smoke test passed!")
