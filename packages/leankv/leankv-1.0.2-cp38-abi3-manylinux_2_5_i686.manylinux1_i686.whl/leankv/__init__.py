from typing import Any, List
import pickle
from . import _leankv
import threading
import time
import atexit
import os

class LeanKVStore:
    """
    A persistent Key-Value store with O(1) lookup.
    Includes background maintenance for persistence.
    """
    def __init__(self, path: str, auto_maintenance: bool = True, check_interval: float = 1.0):
        self._db = _leankv.LeanKV(path)
        self.path = path

        # --- Maintenance / Auto-Vacuum Logic ---
        self.start_time = time.time()
        self.last_access_time = time.time()
        
        # Defaults
        self.maintenance_interval = 86400  # 24 hours
        self.idle_threshold = 3600         # 1 hour
        self._check_interval = check_interval # Configurable for tests
        self.stop_maintenance = False
        
        if auto_maintenance:
            self.m_thread = threading.Thread(target=self._maintenance_loop, daemon=True)
            self.m_thread.start()
            # Ensure data is flushed on script exit
            atexit.register(self.persist)

    def _mark_accessed(self):
        """Updates the last access time to reset the idle timer."""
        self.last_access_time = time.time()

    def _maintenance_loop(self):
        """Background thread to trigger persistence during idle periods."""
        while not self.stop_maintenance:
            time.sleep(self._check_interval)
            
            uptime = time.time() - self.start_time
            idle_time = time.time() - self.last_access_time
            
            # If the DB has been running long enough AND is currently idle
            if uptime > self.maintenance_interval and idle_time > self.idle_threshold:
                try:
                    self.persist()
                    # Reset start time to wait for the next interval
                    self.start_time = time.time()
                except Exception as e:
                    print(f"Auto-maintenance error: {e}")

    def put(self, key: str, value: Any):
        self._mark_accessed()
        serialized = pickle.dumps(value)
        self._db.set_bytes(key, serialized)

    def get(self, key: str, default: Any = None) -> Any:
        self._mark_accessed()
        serialized = self._db.get_bytes(key)
        if serialized is None:
            return default
        try:
            return pickle.loads(serialized)
        except Exception as e:
            print(f"Deserialization error: {e}")
            return None

    def delete(self, key: str) -> bool:
        self._mark_accessed()
        return self._db.delete(key)

    def persist(self):
        if os.path.exists(self.path):
            self._db.persist()

    def vacuum(self):
        self._db.vacuum()

    def keys(self) -> List[str]:
        self._mark_accessed()
        return self._db.keys()

    def close(self):
        """Stop the maintenance thread and persist data."""
        self.stop_maintenance = True
        if hasattr(self, 'm_thread') and self.m_thread.is_alive():
            # Wait at least one check interval to ensure loop exits
            self.m_thread.join(timeout=self._check_interval + 0.5)
        self.persist()

    def __getitem__(self, key: str) -> Any:
        self._mark_accessed()
        serialized = self._db.get_bytes(key)
        if serialized is None:
            raise KeyError(key)
        return pickle.loads(serialized)

    def __setitem__(self, key: str, value: Any):
        self.put(key, value)

    def __delitem__(self, key: str):
        if not self.delete(key):
            raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        self._mark_accessed()
        return self._db.get_bytes(key) is not None

    def __len__(self) -> int:
        self._mark_accessed()
        return self._db.len()
