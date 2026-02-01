from pathlib import Path
import duckdb
import logging
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List

# Note: We avoid importing adbc_driver_duckdb/adbc_driver_manager here to
# keep runtime dependencies light. Use stdlib timezone instead.

from agentfoundry.kgraph.base import KGraphBase
from agentfoundry.vectorstores.factory import VectorStoreFactory

logger = logging.getLogger(__name__)


class DuckSqliteGraph(KGraphBase):
    """Knowledge‑graph implementation backed by DuckDB.

    *Facts* are stored relationally while the accompanying text triple is sent
    to the configured `vector_store` for similarity search.  A light JSON column
    keeps arbitrary metadata keyed by the caller (e.g. `user_id`, `org_id`, etc.).
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, persist_path: str):
        if getattr(self, "_initialized", False):
            return
        path = Path(persist_path)
        path.mkdir(parents=True, exist_ok=True)
        self.db_path = str(path / "kgraph.duckdb")
        self.conn = duckdb.connect(self.db_path)
        self._ensure_schema()
        self.vector_store = VectorStoreFactory.get_store()
        logger.info(f"DuckSqliteGraph initialized at {self.db_path}")
        self._initialized = True

    # ---------------------------------------------------------------------
    # Schema & helpers
    # ---------------------------------------------------------------------
    def _ensure_schema(self) -> None:
        """Create tables / indexes if they do not already exist."""
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS facts (
                id TEXT PRIMARY KEY,
                subject TEXT,
                predicate TEXT,
                obj TEXT,
                user_id TEXT,
                org_id TEXT,
                created_at TIMESTAMP DEFAULT current_timestamp,
                metadata JSON
            )
            """
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_user ON facts(user_id, org_id)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_org_created ON facts(org_id, created_at)"
        )

    @staticmethod
    def _det_id(triple: str, user_id: str, org_id: str) -> str:
        """Deterministically derive the SHA‑256 id from the triple+actor."""
        h = hashlib.sha256()
        h.update(triple.encode())
        h.update(user_id.encode())
        h.update(org_id.encode())
        return h.hexdigest()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def upsert_fact(
        self,
        subject: str,
        predicate: str,
        obj: str,
        metadata: Dict,
    ) -> str:
        """Insert or update a fact and mirror it into the vector store."""
        user_id = metadata.get("user_id", "")
        org_id = metadata.get("org_id", "")
        triple = f"{subject}|{predicate}|{obj}"
        fact_id = self._det_id(triple, user_id, org_id)

        logger.debug(f"Upserting fact id={fact_id} triple={triple}")

        metadata_json = json.dumps(metadata, separators=(",", ":"))
        self.conn.execute(
            "INSERT OR REPLACE INTO facts VALUES (?, ?, ?, ?, ?, ?, current_timestamp, ?)",
            [fact_id, subject, predicate, obj, user_id, org_id, metadata_json],
        )

        # Vector store may throw if the id is already present – swallow and carry on
        try:
            self.vector_store.add_texts([triple], metadatas=[metadata], ids=[fact_id])
        except ValueError:
            pass

        return fact_id

    def search(
        self,
        query: str,
        *,
        user_id: str,
        org_id: str,
        k: int = 5,
    ) -> List[Dict]:
        logger.debug(
            f"KG search query='{query}' user={user_id} org={org_id} k={k}"
        )
        docs = self.vector_store.similarity_search_with_score(
            query, k=k, filter={"user_id": user_id, "org_id": org_id}
        )

        results = []
        for doc, score in docs:
            subj, pred, obj = doc.page_content.split("|", 2)
            results.append(
                {"subject": subj, "predicate": pred, "object": obj, "score": score}
            )
        logger.info(f"KG search returned {len(results)} results")
        return results

    def get_neighbours(self, entity: str, depth: int = 2) -> List[Dict]:
        """Breadth‑first traversal up to *depth* hops from *entity*."""
        q = """
        WITH RECURSIVE hop(n, s, p, o) AS (
            SELECT 1, subject, predicate, obj FROM facts
            WHERE subject = ? OR obj = ?
            UNION ALL
            SELECT n + 1, f.subject, f.predicate, f.obj
            FROM facts f
            JOIN hop h ON f.subject = h.o
            WHERE n < ?
        )
        SELECT s, p, o FROM hop;
        """
        logger.debug(f"Fetching neighbours for {entity} depth={depth}")
        rows = self.conn.execute(q, [entity, entity, depth]).fetchall()
        return [
            {"subject": s, "predicate": p, "object": o} for s, p, o in rows
        ]

    def purge_expired(self, days: int = 90) -> None:
        """Remove facts whose *created_at* is older than *days*."""
        logger.info("Purging facts older than %d days", days)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        self.conn.execute("DELETE FROM facts WHERE created_at < ?", [cutoff])

    def delete_context(self, *, org_id: str, graph_slice_id: str) -> int:
        """Delete all triples linked to a particular graph slice id."""
        logger.info("Deleting graph slice %s for org %s", graph_slice_id, org_id)
        result = self.conn.execute(
            """
            DELETE FROM facts
            WHERE org_id = ?
              AND json_extract(metadata, '$.graph_slice_id') = ?
            """,
            [org_id, graph_slice_id],
        )
        return result.rowcount if hasattr(result, "rowcount") else 0

    def fetch_by_metadata(self, *, org_id: str, filters: Dict[str, str]) -> List[Dict]:
        """Fetch triples whose metadata JSON includes the supplied key/value filters."""
        params = [org_id]
        conditions = ["org_id = ?"]
        for key, value in filters.items():
            conditions.append("json_extract(metadata, ?) = ?")
            params.append(f"$.{key}")
            params.append(value)

        where_clause = " AND ".join(conditions)
        query = f"SELECT subject, predicate, obj, metadata FROM facts WHERE {where_clause}"
        rows = self.conn.execute(query, params).fetchall()
        results: List[Dict] = []
        for subject, predicate, obj, metadata in rows:
            try:
                meta = json.loads(metadata) if isinstance(metadata, str) else metadata
            except Exception:
                meta = {}
            results.append(
                {
                    "subject": subject,
                    "predicate": predicate,
                    "object": obj,
                    "metadata": meta,
                }
            )
        return results
