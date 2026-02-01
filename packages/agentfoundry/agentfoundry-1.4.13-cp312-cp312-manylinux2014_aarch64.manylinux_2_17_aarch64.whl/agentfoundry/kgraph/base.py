
# agentfoundry/kgraph/base.py

from abc import ABC, abstractmethod
from typing import Dict, List

class KGraphBase(ABC):
    """Abstract knowledge-graph interface shielding clients from providers."""

    @abstractmethod
    def upsert_fact(self, subject: str, predicate: str, obj: str,
                    metadata: Dict) -> str:
        pass

    @abstractmethod
    def search(self, query: str, *, user_id: str, org_id: str,
               k: int = 5) -> List[Dict]:
        pass

    @abstractmethod
    def get_neighbours(self, entity: str, depth: int = 2) -> List[Dict]:
        pass

    @abstractmethod
    def purge_expired(self, days: int = 90) -> None:
        pass

    @abstractmethod
    def delete_context(self, *, org_id: str, graph_slice_id: str) -> int:
        """Remove facts associated with a persisted graph slice."""
        pass

    @abstractmethod
    def fetch_by_metadata(self, *, org_id: str, filters: Dict[str, str]) -> List[Dict]:
        """Return triples whose metadata contains the supplied key/value pairs."""
        pass

