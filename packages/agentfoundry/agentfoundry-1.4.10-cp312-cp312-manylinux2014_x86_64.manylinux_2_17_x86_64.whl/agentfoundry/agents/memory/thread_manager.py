import os
import pathlib
import logging
from typing import Optional
from agentfoundry.utils.agent_config import AgentConfig

logger = logging.getLogger(__name__)

class ThreadManager:
    """
    Manages thread lifecycle and discovery.
    """
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig.from_legacy_config()
        self.config = config
        
        # Determine root data dir matching ThreadMemory logic
        data_dir = config.data_dir or "./data"
        self.root = pathlib.Path(data_dir) / "memory_cache" / "threads"

    def get_latest_thread(self, user_id: str, org_id: str) -> Optional[str]:
        """
        Find the most recently modified thread ID for a user.
        Returns None if no threads exist.
        """
        # Path structure: root / org_{org_id} / {user_id} / {thread_id}
        # Note: ThreadMemory uses "org_{org_id}" prefix in the path.
        user_path = self.root / f"org_{org_id}" / user_id
        
        if not user_path.exists():
            return None
            
        # List subdirectories (threads)
        threads = [p for p in user_path.iterdir() if p.is_dir()]
        if not threads:
            return None
            
        # Sort by modification time descending (newest first)
        threads.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        
        latest = threads[0].name
        logger.info(f"Found latest thread for {user_id}: {latest}")
        return latest

    def generate_next_thread_id(self, user_id: str, org_id: str) -> str:
        """
        Generate the next sequential thread ID.
        If previous threads were "1", "2", returns "3".
        Defaults to "1" if no threads exist.
        """
        user_path = self.root / f"org_{org_id}" / user_id
        
        if not user_path.exists():
             return "1"
             
        threads = [p.name for p in user_path.iterdir() if p.is_dir()]
        
        # Find max integer ID
        max_id = 0
        has_int_ids = False
        for t in threads:
            if t.isdigit():
                has_int_ids = True
                val = int(t)
                if val > max_id:
                    max_id = val
        
        if has_int_ids:
            return str(max_id + 1)
            
        # If existing threads are not integers (e.g. UUIDs), failover to "1"
        # unless "1" happens to exist as a string
        if "1" not in threads:
            return "1"
            
        # Fallback for mixed state
        import uuid
        return f"thread_{uuid.uuid4().hex[:8]}"
