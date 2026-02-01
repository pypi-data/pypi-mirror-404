from __future__ import annotations
import requests
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
import logging

logger = logging.getLogger(__name__)


class GeoLocationInput(BaseModel):
    """
    No input parameters required. Query for geolocation of the current machine.
    """
    pass


class GeoLocationResult(BaseModel):
    ip: str = Field(..., description="Public IP address of the machine")
    city: str = Field(..., description="City of the machine's location")
    region: str = Field(..., description="Region or state of the machine's location")
    country: str = Field(..., description="Country code (e.g., 'US')")
    loc: str = Field(..., description="Latitude and longitude coordinates as 'lat,long'")
    postal: str = Field(..., description="Postal code of the location")
    timezone: str = Field(..., description="Timezone of the location")
    org: str = Field(..., description="Organization or ISP information")


def get_geo_location() -> GeoLocationResult:
    """
    Retrieves geolocation data for the current machine based on its public IP using the ipinfo.io API.
    """
    logger.info("Fetching geolocation for current machine")
    try:
        response = requests.get("https://ipinfo.io/json")
        response.raise_for_status()
        data = response.json()
        return GeoLocationResult(**data)
    except Exception as ex:
        logger.error(f"Error fetching geo location: {ex}")
        raise


# Structured LangChain tool
geo_location_tool = StructuredTool.from_function(
    func=get_geo_location,
    name="geo_location_tool",
    description="Determines the geographic location of the current machine based on its public IP address.",
    args_schema=GeoLocationInput
)
