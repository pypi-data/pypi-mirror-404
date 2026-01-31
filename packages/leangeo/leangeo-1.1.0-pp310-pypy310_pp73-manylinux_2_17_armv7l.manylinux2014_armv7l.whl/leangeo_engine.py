import orjson
import leangeo
import logging
import atexit
import time
import threading
import math
import gc
import os
import fcntl
from typing import Union, List, Tuple, Optional, Any
from contextlib import contextmanager

# Set up basic logging
logger = logging.getLogger(__name__)

# --- Locks and Trackers from reference.py ---

class CollectionLock:
    """File-based lock for a collection, providing both thread and process safety."""
    
    def __init__(self, collection_path: str):
        self.lock_path = os.path.join(collection_path, '.collection.lock')
        self.lock_file = None
        self._thread_lock = threading.RLock()
        self._ensure_lock_file()
    
    def _ensure_lock_file(self):
        """Ensure the lock file exists."""
        os.makedirs(os.path.dirname(self.lock_path), exist_ok=True)
        if not os.path.exists(self.lock_path):
            open(self.lock_path, 'a').close()
    
    @contextmanager
    def read_lock(self):
        """Acquire a shared read lock (thread-safe and process-safe)."""
        with self._thread_lock:
            self._ensure_lock_file()
            self.lock_file = open(self.lock_path, 'r')
            try:
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_SH)
                yield
            finally:
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                self.lock_file.close()
                self.lock_file = None
    
    @contextmanager
    def write_lock(self):
        """Acquire an exclusive write lock (thread-safe and process-safe)."""
        with self._thread_lock:
            self._ensure_lock_file()
            self.lock_file = open(self.lock_path, 'r')
            try:
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX)
                yield
            finally:
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                self.lock_file.close()
                self.lock_file = None

class NoOpLock:
    """No-op lock that does nothing - for single-threaded use."""
    
    @contextmanager
    def read_lock(self):
        yield
    
    @contextmanager
    def write_lock(self):
        yield

class VersionTracker:
    """Track collection version to detect changes from other processes."""
    
    def __init__(self, collection_path: str):
        self.version_path = os.path.join(collection_path, '.version')
        self._ensure_version_file()
    
    def _ensure_version_file(self):
        """Ensure version file exists."""
        os.makedirs(os.path.dirname(self.version_path), exist_ok=True)
        if not os.path.exists(self.version_path):
            self._write_version(0)
    
    def _write_version(self, version: int):
        """Write version atomically."""
        with open(self.version_path, 'w') as f:
            f.write(str(version))
            f.flush()
            os.fsync(f.fileno())
    
    def get_version(self) -> int:
        """Get current version."""
        try:
            with open(self.version_path, 'r') as f:
                return int(f.read().strip())
        except (FileNotFoundError, ValueError):
            return 0
    
    def increment_version(self):
        """Increment version (call after writes)."""
        current = self.get_version()
        self._write_version(current + 1)

class NoOpVersionTracker:
    """No-op version tracker that does nothing - for single-threaded use."""
    
    def get_version(self) -> int:
        return 0
    
    def increment_version(self):
        pass

# --- Main Engine ---

class LeanGeoEngine:
    """
    An enhanced Python wrapper for the Rust-based LeanGeo geospatial database.
    Includes auto-persistence, background maintenance, metadata sanitization,
    and optional thread/process safety.
    """
    def __init__(self, storage_path: str, auto_persist: bool = True, thread_safe: bool = False):
        self.base_path = storage_path
        self.thread_safe = thread_safe
        
        # Initialize locking and version tracking
        if self.thread_safe:
            if not os.path.exists(storage_path):
                os.makedirs(storage_path)
            self.lock = CollectionLock(storage_path)
            self.tracker = VersionTracker(storage_path)
        else:
            self.lock = NoOpLock()
            self.tracker = NoOpVersionTracker()
        
        # Initial load
        self._inner = leangeo.LeanGeo(storage_path)
        self.local_version = self.tracker.get_version()
        
        # Maintenance state
        self.last_access_time = time.time()
        self.start_time = time.time()
        self.maintenance_interval = 86400  # 24 hours
        self.idle_threshold = 3600         # 1 hour
        self.stop_maintenance = False
        
        # Start background maintenance thread
        self.m_thread = threading.Thread(target=self._maintenance_loop, daemon=True)
        self.m_thread.start()
        
        # Register exit handler
        if auto_persist:
            atexit.register(self.persist)

    # --- Safety Helpers ---

    def _needs_reload(self) -> bool:
        """Check if collection needs to be reloaded (always False if not thread_safe)."""
        if not self.thread_safe:
            return False
        
        disk_version = self.tracker.get_version()
        return disk_version > self.local_version

    def _reload(self):
        """Reload the DB from disk (no-op if not thread_safe)."""
        if not self.thread_safe:
            return
        
        # Assuming leangeo.LeanGeo handles reloading by re-instantiation 
        # or that we replace the handle.
        self._inner = leangeo.LeanGeo(self.base_path)
        self.local_version = self.tracker.get_version()

    def _update_version_after_write(self):
        """Increments version on disk and updates local version (if thread_safe)."""
        if self.thread_safe:
            self.tracker.increment_version()
            self.local_version = self.tracker.get_version()

    # --- Utils ---

    def _ensure_json_string(self, data: Union[str, dict, None]) -> Optional[str]:
        """Sanitizes and converts dict to JSON string for Rust consumption."""
        if data is None:
            return None
        if isinstance(data, dict):
            # Sanitize to handle NaN/Inf before serialization
            sanitized = self._sanitize_metadata(data)
            # orjson.dumps returns bytes, must decode for Rust string compatibility
            return orjson.dumps(sanitized).decode('utf-8')
        return data

    def _sanitize_metadata(self, meta: Any) -> Any:
        """Recursively cleans metadata to ensure JSON compatibility (NaN -> None)."""
        if isinstance(meta, float):
            if math.isnan(meta) or math.isinf(meta):
                return None
        elif isinstance(meta, dict):
            return {k: self._sanitize_metadata(v) for k, v in meta.items()}
        elif isinstance(meta, list):
            return [self._sanitize_metadata(v) for v in meta]
        return meta

    def _parse_json_result(self, metadata_str: str) -> dict:
        """Safely converts a JSON string from Rust back to a Python dict."""
        if not metadata_str:
            return {}
        try:
            return orjson.loads(metadata_str)
        except (orjson.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to parse metadata: {metadata_str}. Error: {e}")
            return {"raw_error": str(e), "raw_data": metadata_str}

    def _update_access_time(self):
        self.last_access_time = time.time()

    def _maintenance_loop(self):
        """Background loop to persist data during idle periods."""
        while not self.stop_maintenance:
            time.sleep(60) # Check every minute
            uptime = time.time() - self.start_time
            idle_time = time.time() - self.last_access_time
            
            # If system has been up long enough and is currently idle
            if uptime > self.maintenance_interval and idle_time > self.idle_threshold:
                try:
                    self.persist()
                    # Reset maintenance clock
                    self.start_time = time.time()
                except Exception as e:
                    logger.error(f"Background maintenance failed: {e}")

    # --- Write Operations ---

    def add(self, id: str, lat: float, lon: float, metadata: Union[str, dict]) -> None:
        self._update_access_time()
        
        with self.lock.write_lock():
            # Reload if thread_safe
            if self.thread_safe and self._needs_reload():
                self._reload()
            
            meta_str = self._ensure_json_string(metadata)
            self._inner.add(id, float(lat), float(lon), meta_str)
            
            # Persist and version tracking (only if thread_safe)
            if self.thread_safe:
                self._inner.persist()
                self._update_version_after_write()

    def persist(self) -> None:
        """Explicitly save data to disk."""
        with self.lock.write_lock():
            # If thread safe, reload first to ensure we aren't overwriting newer data from elsewhere
            if self.thread_safe and self._needs_reload():
                self._reload()

            try:
                gc.collect() # Trigger GC before heavy IO/Persistence
                self._inner.persist()
                
                # Version tracking
                if self.thread_safe:
                    self._update_version_after_write()
            except Exception as e:
                logger.error(f"Persist failed: {e}")

    def vacuum(self) -> None:
        """Stop-the-world compaction to optimize storage."""
        self._update_access_time()
        
        with self.lock.write_lock():
            if self.thread_safe and self._needs_reload():
                self._reload()
                
            self._inner.vacuum()
            
            if self.thread_safe:
                self._update_version_after_write()

    def delete(self, id: str) -> None:
        self._update_access_time()
        
        with self.lock.write_lock():
            if self.thread_safe and self._needs_reload():
                self._reload()
                
            self._inner.delete(id)
            
            if self.thread_safe:
                self._inner.persist()
                self._update_version_after_write()

    def delete_by_filter(self, filter_json: Union[str, dict]) -> int:
        self._update_access_time()
        
        with self.lock.write_lock():
            if self.thread_safe and self._needs_reload():
                self._reload()
            
            f_str = self._ensure_json_string(filter_json)
            count = self._inner.delete_by_filter(f_str)
            
            if self.thread_safe:
                self._inner.persist()
                self._update_version_after_write()
                
            return count

    # --- Read Operations ---

    def count(self) -> int:
        # Check if reload is needed (only if thread_safe)
        if self.thread_safe and self._needs_reload():
            with self.lock.write_lock():
                if self._needs_reload():
                    self._reload()
                return self._inner.count()
        else:
            with self.lock.read_lock():
                return self._inner.count()

    def search_knn(self, lat: float, lon: float, k: int, filter_json: Union[str, dict, None] = None) -> List[Tuple[str, float, dict]]:
        self._update_access_time()
        
        # If thread_safe and reload needed, use write lock to update
        if self.thread_safe and self._needs_reload():
            with self.lock.write_lock():
                if self._needs_reload():
                    self._reload()
                f_str = self._ensure_json_string(filter_json)
                results = self._inner.search_knn(float(lat), float(lon), int(k), f_str)
        else:
            with self.lock.read_lock():
                f_str = self._ensure_json_string(filter_json)
                results = self._inner.search_knn(float(lat), float(lon), int(k), f_str)
                
        return [(r[0], r[1], self._parse_json_result(r[2])) for r in results]

    def search_radius(self, lat: float, lon: float, radius_m: float, filter_json: Union[str, dict, None] = None) -> List[Tuple[str, float, dict]]:
        self._update_access_time()

        if self.thread_safe and self._needs_reload():
            with self.lock.write_lock():
                if self._needs_reload():
                    self._reload()
                f_str = self._ensure_json_string(filter_json)
                results = self._inner.search_radius(float(lat), float(lon), float(radius_m), f_str)
        else:
            with self.lock.read_lock():
                f_str = self._ensure_json_string(filter_json)
                results = self._inner.search_radius(float(lat), float(lon), float(radius_m), f_str)

        return [(r[0], r[1], self._parse_json_result(r[2])) for r in results]

    def search_box(self, top_left: Tuple[float, float], bottom_right: Tuple[float, float], filter_json: Union[str, dict, None] = None) -> List[Tuple[str, dict]]:
        self._update_access_time()

        if self.thread_safe and self._needs_reload():
            with self.lock.write_lock():
                if self._needs_reload():
                    self._reload()
                f_str = self._ensure_json_string(filter_json)
                results = self._inner.search_box(top_left, bottom_right, f_str)
        else:
            with self.lock.read_lock():
                f_str = self._ensure_json_string(filter_json)
                results = self._inner.search_box(top_left, bottom_right, f_str)

        return [(r[0], self._parse_json_result(r[1])) for r in results]

    def search_bbox(self, min_lat: float, max_lat: float, min_lon: float, max_lon: float, filter_json: Union[str, dict, None] = None) -> List[str]:
        top_left = (max_lat, min_lon)
        bottom_right = (min_lat, max_lon)
        # Relies on search_box which handles locking
        results = self.search_box(top_left, bottom_right, filter_json)
        return [r[0] for r in results]

    def search_polygon(self, points: List[Tuple[float, float]], filter_json: Union[str, dict, None] = None) -> List[Tuple[str, dict]]:
        self._update_access_time()

        if self.thread_safe and self._needs_reload():
            with self.lock.write_lock():
                if self._needs_reload():
                    self._reload()
                f_str = self._ensure_json_string(filter_json)
                results = self._inner.search_polygon(points, f_str)
        else:
            with self.lock.read_lock():
                f_str = self._ensure_json_string(filter_json)
                results = self._inner.search_polygon(points, f_str)

        return [(r[0], self._parse_json_result(r[1])) for r in results]

    def close(self):
        """Gracefully close the database."""
        self.stop_maintenance = True
        if self.m_thread.is_alive():
            self.m_thread.join(timeout=5)
        self.persist()
