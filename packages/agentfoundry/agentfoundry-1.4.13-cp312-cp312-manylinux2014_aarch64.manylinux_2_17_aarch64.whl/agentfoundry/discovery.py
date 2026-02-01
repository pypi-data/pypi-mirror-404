__author__ = "Chris Steel"
__copyright__ = "Copyright 2025, Syntheticore Corporation"
__credits__ = ["Chris Steel"]
__date__ = "2/8/2025"
__license__ = "Syntheticore Confidential"
__version__ = "1.0"
__email__ = "csteel@syntheticore.com"
__status__ = "Production"

import logging
import warnings

import requests

from agentfoundry.utils.agent_config import AgentConfig


class Discovery:
    """
    A class for discovering APIs based on a search query.

    Requires a configured external search API (e.g., SerpAPI) and will
    raise if the required configuration is missing, rather than simulating
    discovery.
    """

    def __init__(self, config: AgentConfig = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Handle backward compatibility
        if config is None:
            warnings.warn(
                "Discovery() without config is deprecated. Pass AgentConfig explicitly.",
                DeprecationWarning,
                stacklevel=2
            )
            config = AgentConfig.from_legacy_config()
        
        self._config = config
        
        # Get SERPAPI key from config
        self.search_api_key = config.serpapi_api_key.get_secret_value() if config.serpapi_api_key else None
        if not self.search_api_key:
            self.logger.warning("No SERPAPI_API_KEY found in configuration. API discovery may be limited.")
            raise Exception("No SERPAPI_API_KEY found in configuration. API discovery will not work.")
        self.search_engine_url = "https://serpapi.com/search"  # Example endpoint for SerpAPI
        self.logger.info("Discovery agent initialized.")

    def discover_apis(self, query: str):
        """
        Discover APIs relevant to the provided query.

        Args:
            query (str): The search query (e.g., "LinkedIn API documentation").

        Returns:
            list: A list of dictionaries, each containing details about a discovered API.
                  Expected keys include 'name', 'base_url', and 'documentation_url'.
        """
        self.logger.info(f"Discovering APIs for query: {query}")

        if not self.search_api_key:
            self.logger.warning("No SerpAPI key – skipping discovery.")
            return []

        discovered_apis = []
        # If a search API key is provided, you could perform a real search.
        if self.search_api_key:
            params = {
                "q": query,
                "api_key": self.search_api_key,
                "engine": "google",
                "hl": "en"
            }
        else:
            params = {}
        try:
            resp = requests.get(self.search_engine_url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            self.logger.error(f"API-discovery HTTP/JSON error: {exc}", exc_info=True)
            return []

        # ---- pick the list that actually contains hits ---------------------------
        candidates = []
        # normal Google results if SerpAPI found any
        candidates.extend(data.get("organic_results", []))
        # some queries return nothing but “related_questions”
        if not candidates:
            candidates.extend(data.get("related_questions", []))
        # …or “related_searches”
        if not candidates:
            candidates.extend(data.get("related_searches", []))

        apis: list[dict] = []
        for item in candidates:
            title = item.get("title") or item.get("question") or item.get("query")
            link = item.get("link") or item.get("displayed_link")
            if title and link:
                apis.append(
                    {
                        "name": title,
                        "base_url": link,
                        "documentation_url": link,  # refine later if you have a doc URL
                    }
                )
        return apis

    # Optionally, implement a helper method to process search results.
    # def _process_search_results(self, data: dict) -> list:
    #     # Parse the JSON returned from the search API to extract API details.
    #     # This is highly dependent on the response format of your chosen search API.
    #     discovered = []
    #     # Example processing logic (to be implemented):
    #     # for result in data.get("results", []):
    #     #     api_info = {
    #     #         "name": result.get("title"),
    #     #         "base_url": extract_base_url(result.get("link")),
    #     #         "documentation_url": result.get("link")
    #     #     }
    #     #     discovered.append(api_info)
    #     # return discovered
    #     return discovered


# Simple test if the module is executed directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    discovery = Discovery()
    apis = discovery.discover_apis("REST API no api key required")
    print("Discovered APIs:")
    for api in apis:
        print(api)
