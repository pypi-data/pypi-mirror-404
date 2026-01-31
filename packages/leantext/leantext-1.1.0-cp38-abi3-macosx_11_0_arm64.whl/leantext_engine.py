import orjson
import uuid
import os
import re
import leantext
import atexit
import gc
import time
import threading
import copy
import math
import fcntl
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

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

class LeanTextEngine:
    """
    A high-level wrapper for LeanText that supports:
    - Multiple collections (subdirectories).
    - Automatic background persistence (maintenance loop).
    - Metadata sanitization (NaN handling).
    - Batch operations.
    - Automatic cleanup on exit.
    - Optional thread and process safety.
    """
    
    def __init__(self, base_path: str = 'leantext_root', auto_persist: bool = True, thread_safe: bool = False):
        """Initialize LeanTextEngine.
        
        Args:
            base_path: Directory to store database files
            auto_persist: Whether to automatically persist on exit
            thread_safe: If True, enables thread and process safety with locking and version tracking.
                        If False, disables all safety mechanisms for maximum performance in single-threaded scenarios.
        """
        self.base_path = base_path
        self.thread_safe = thread_safe
        
        if not os.path.exists(base_path):
            os.makedirs(base_path)
            
        self.collections: Dict[str, leantext.LeanText] = {}
        self.collection_locks: Dict[str, CollectionLock] = {}
        self.version_trackers: Dict[str, VersionTracker] = {}
        self.local_versions: Dict[str, int] = {}
        
        # Global lock for managing collections dict (only if thread_safe)
        self._collections_lock = threading.RLock() if thread_safe else None
        
        # Maintenance settings
        self.start_time = time.time()
        self.last_access_time = time.time()
        self.maintenance_interval = 86400  # 24 hours
        self.idle_threshold = 3600         # 1 hour
        self.stop_maintenance = False
        
        self.m_thread = threading.Thread(target=self._maintenance_loop, daemon=True)
        self.m_thread.start()
        
        if auto_persist:
            atexit.register(self.persist_all)
    
    def _get_col_path(self, name: str) -> str:
        return os.path.join(self.base_path, name)
    
    def _get_collection_lock(self, name: str):
        """Get or create a lock for a collection (or no-op if not thread_safe)."""
        if not self.thread_safe:
            return NoOpLock()
        
        with self._collections_lock:
            if name not in self.collection_locks:
                path = self._get_col_path(name)
                self.collection_locks[name] = CollectionLock(path)
            return self.collection_locks[name]
    
    def _get_version_tracker(self, name: str):
        """Get or create a version tracker for a collection (or no-op if not thread_safe)."""
        if not self.thread_safe:
            return NoOpVersionTracker()
        
        with self._collections_lock:
            if name not in self.version_trackers:
                path = self._get_col_path(name)
                self.version_trackers[name] = VersionTracker(path)
            return self.version_trackers[name]
    
    def _needs_reload(self, collection: str) -> bool:
        """Check if collection needs to be reloaded (always False if not thread_safe)."""
        if not self.thread_safe:
            return False
        
        if collection not in self.local_versions:
            return True
        
        tracker = self._get_version_tracker(collection)
        disk_version = tracker.get_version()
        return disk_version > self.local_versions.get(collection, -1)
    
    def _reload_collection(self, collection: str):
        """Reload a collection from disk (no-op if not thread_safe)."""
        if not self.thread_safe:
            return
        
        if self._collections_lock:
            with self._collections_lock:
                if collection in self.collections:
                    del self.collections[collection]
                
                path = self._get_col_path(collection)
                self.collections[collection] = leantext.LeanText(path)
                
                tracker = self._get_version_tracker(collection)
                self.local_versions[collection] = tracker.get_version()
        else:
            if collection in self.collections:
                del self.collections[collection]
            
            path = self._get_col_path(collection)
            self.collections[collection] = leantext.LeanText(path)
            
            tracker = self._get_version_tracker(collection)
            self.local_versions[collection] = tracker.get_version()
    
    def _ensure_collection(self, name: str) -> leantext.LeanText:
        """Thread-safe collection initialization (or simple init if not thread_safe)."""
        self.last_access_time = time.time()
        
        if self.thread_safe and self._collections_lock:
            with self._collections_lock:
                if name not in self.collections:
                    path = self._get_col_path(name)
                    if not os.path.exists(path):
                        os.makedirs(path)
                    self.collections[name] = leantext.LeanText(path)
                    
                    tracker = self._get_version_tracker(name)
                    self.local_versions[name] = tracker.get_version()
        else:
            # Non-thread-safe path - no locking
            if name not in self.collections:
                path = self._get_col_path(name)
                if not os.path.exists(path):
                    os.makedirs(path)
                self.collections[name] = leantext.LeanText(path)
        
        return self.collections[name]
    
    def list_collections(self) -> List[str]:
        """Lists subdirectories in base_path that look like collections."""
        if self.thread_safe and self._collections_lock:
            with self._collections_lock:
                cols = set(self.collections.keys())
        else:
            cols = set(self.collections.keys())
        
        if os.path.exists(self.base_path):
            for name in os.listdir(self.base_path):
                if os.path.isdir(self._get_col_path(name)):
                    cols.add(name)
        return list(cols)
    
    def add(self, content: str, title: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None, doc_id: Optional[str] = None, collection: str = "default") -> str:
        """Adds a single document. Returns the document ID."""
        return self.add_batch([content], [title] if title else None, [metadata] if metadata else None, [doc_id] if doc_id else None, collection)[0]
    
    def add_batch(
        self,
        contents: List[str],
        titles: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        collection: str = "default"
    ) -> List[str]:
        """Batch insert with optional thread/process safety."""
        if not contents:
            return []
        
        col_lock = self._get_collection_lock(collection)
        
        with col_lock.write_lock():
            # Only reload if thread_safe
            if self.thread_safe and self._needs_reload(collection):
                self._reload_collection(collection)
            
            db = self._ensure_collection(collection)
            
            # Prepare inputs
            if metadatas is None:
                metadatas = [{} for _ in range(len(contents))]
            if ids is None:
                ids = [None] * len(contents)
            
            result_ids = []
            
            for i, text in enumerate(contents):
                # Metadata handling
                meta_orig = metadatas[i] if i < len(metadatas) else {}
                meta = copy.deepcopy(meta_orig) if meta_orig else {}
                meta = self._sanitize_metadata(meta)
                
                # Title handling
                title = titles[i] if titles and i < len(titles) else None

                # ID handling
                provided_id = ids[i] if i < len(ids) else None
                doc_id = str(provided_id or meta.get("id") or meta.get("_id") or uuid.uuid4())
                meta["id"] = doc_id
                
                # Serialization safety
                try:
                    meta_json = orjson.dumps(meta).decode('utf-8')
                except orjson.JSONEncodeError:
                    meta_json = orjson.dumps({"id": doc_id}).decode('utf-8')
                
                # Update: Pass title to Rust
                db.add(doc_id, text, title, meta_json)
                result_ids.append(doc_id)
            
            # Persist and version tracking (only if thread_safe)
            if self.thread_safe:
                db.persist()
                tracker = self._get_version_tracker(collection)
                tracker.increment_version()
                
                if self._collections_lock:
                    with self._collections_lock:
                        self.local_versions[collection] = tracker.get_version()
                else:
                    self.local_versions[collection] = tracker.get_version()
            
            return result_ids
    
    def _sanitize_metadata(self, meta: Any) -> Any:
        """Recursively cleans metadata for JSON compatibility (handles NaN/Inf)."""
        if isinstance(meta, float):
            if math.isnan(meta) or math.isinf(meta):
                return None
        elif isinstance(meta, dict):
            return {k: self._sanitize_metadata(v) for k, v in meta.items()}
        elif isinstance(meta, list):
            return [self._sanitize_metadata(v) for v in meta]
        return meta
    
    def _highlight(self, content: str, query: str) -> Optional[str]:
        if not content or not query:
            return None

        query_tokens = query.lower().split()
        if not query_tokens:
            return None

        escaped_tokens = [re.escape(t) for t in query_tokens]
        # Use simple word boundary check
        pattern_str = r'\b(' + '|'.join(escaped_tokens) + r')\b'
        try:
            pattern = re.compile(pattern_str, re.IGNORECASE)
        except re.error:
            return None

        matches = list(pattern.finditer(content))
        if not matches:
            return None

        # Find window with most matches.
        # For simplicity and performance, checking windows around each match.
        window_size = 150
        best_score = -1
        best_start = 0

        # Optimization: Don't check every single match if there are too many.
        # But usually search results are small enough.

        for m in matches:
            start = max(0, m.start() - 60)
            end = start + window_size
            snippet = content[start:end]

            score = 0
            # Count distinct tokens found in snippet
            snippet_lower = snippet.lower()
            for t in query_tokens:
                if t in snippet_lower:
                    score += 1

            if score > best_score:
                best_score = score
                best_start = start

        # Adjust boundaries
        start_idx = best_start
        end_idx = min(len(content), start_idx + window_size)

        # Snap to space
        if start_idx > 0:
            prev_space = content.rfind(' ', 0, start_idx + 10)
            if prev_space != -1 and prev_space >= start_idx - 10:
                start_idx = prev_space + 1

        if end_idx < len(content):
            next_space = content.find(' ', end_idx - 10)
            if next_space != -1 and next_space <= end_idx + 10:
                end_idx = next_space

        snippet = content[start_idx:end_idx]
        highlighted = pattern.sub(r'<em>\1</em>', snippet)
        return highlighted

    def search(
        self, 
        query: str, 
        k: int = 10, 
        filters: Optional[Dict[str, Any]] = None, 
        collection: str = "default", 
        fuzzy_dist: int = 0,
        title_boost: float = 1.0,
        body_boost: float = 1.0,
        return_content: bool = False,
        force_fresh: bool = False,
        return_highlight: bool = False
    ) -> List[Dict[str, Any]]:
        """Search with optional thread/process safety."""
        
        col_lock = self._get_collection_lock(collection)
        
        # Determine if we need to fetch content
        fetch_content = return_content or return_highlight

        # If thread_safe and (force_fresh or reload needed), use write lock
        if self.thread_safe and (force_fresh or self._needs_reload(collection)):
            with col_lock.write_lock():
                if self._needs_reload(collection):
                    self._reload_collection(collection)
                
                db = self._ensure_collection(collection)
                filter_str = orjson.dumps(filters).decode('utf-8') if filters else None
                
                # Returns: Vec<(String, f32, String, String, Option<String>)>
                raw_results = db.search(
                    query, 
                    filter_str, 
                    k, 
                    fuzzy_dist, 
                    title_boost, 
                    body_boost, 
                    fetch_content
                )
        else:
            # No reload needed or not thread_safe, use read lock (or no-op lock)
            with col_lock.read_lock():
                db = self._ensure_collection(collection)
                filter_str = orjson.dumps(filters).decode('utf-8') if filters else None
                
                raw_results = db.search(
                    query, 
                    filter_str, 
                    k, 
                    fuzzy_dist, 
                    title_boost, 
                    body_boost, 
                    fetch_content
                )
        
        results = []
        for doc_id, score, title, meta_str, content in raw_results:
            try:
                meta = orjson.loads(meta_str)
            except (TypeError, orjson.JSONDecodeError):
                meta = {}
            
            res = {
                "id": doc_id,
                "score": score,
                "title": title,
                "metadata": meta
            }
            if return_content:
                res["content"] = content
            
            if return_highlight and content:
                hl = self._highlight(content, query)
                if hl:
                    res["highlight"] = hl

            results.append(res)
        return results
    
    def get_content(self, doc_id: str, collection: str = "default") -> Optional[str]:
        """Get content with optional thread/process safety."""
        if collection not in self.collections:
            # Try loading if it exists on disk
            path = self._get_col_path(collection)
            if not os.path.exists(path):
                return None
        
        col_lock = self._get_collection_lock(collection)
        
        # Check if reload is needed (only if thread_safe)
        if self.thread_safe and self._needs_reload(collection):
            with col_lock.write_lock():
                if self._needs_reload(collection):
                    self._reload_collection(collection)
                return self._ensure_collection(collection).get_content(doc_id)
        else:
            with col_lock.read_lock():
                return self._ensure_collection(collection).get_content(doc_id)
    
    def delete(self, doc_id: str, collection: str = "default") -> None:
        """Delete with optional thread/process safety."""
        if collection not in self.collections and not os.path.exists(self._get_col_path(collection)):
            return
        
        col_lock = self._get_collection_lock(collection)
        
        with col_lock.write_lock():
            # Reload if thread_safe
            if self.thread_safe and self._needs_reload(collection):
                self._reload_collection(collection)
            
            self._ensure_collection(collection).delete(doc_id)
            
            # Persist and version tracking (only if thread_safe)
            if self.thread_safe:
                self.collections[collection].persist()
                tracker = self._get_version_tracker(collection)
                tracker.increment_version()
                
                if self._collections_lock:
                    with self._collections_lock:
                        self.local_versions[collection] = tracker.get_version()
                else:
                    self.local_versions[collection] = tracker.get_version()
    
    def delete_by_filter(self, metadata_filter: Dict[str, Any], collection: str = "default") -> int:
        """Delete by filter with optional thread/process safety."""
        if collection not in self.collections and not os.path.exists(self._get_col_path(collection)):
            return 0
        
        col_lock = self._get_collection_lock(collection)
        
        with col_lock.write_lock():
            # Reload if thread_safe
            if self.thread_safe and self._needs_reload(collection):
                self._reload_collection(collection)
            
            db = self._ensure_collection(collection)
            count = db.delete_by_filter(orjson.dumps(metadata_filter).decode('utf-8'))
            
            # Persist and version tracking (only if thread_safe)
            if self.thread_safe:
                db.persist()
                tracker = self._get_version_tracker(collection)
                tracker.increment_version()
                
                if self._collections_lock:
                    with self._collections_lock:
                        self.local_versions[collection] = tracker.get_version()
                else:
                    self.local_versions[collection] = tracker.get_version()
            
            return count
    
    def count(self, collection: str = "default") -> int:
        """Count with optional thread/process safety."""
        if collection not in self.collections and not os.path.exists(self._get_col_path(collection)):
            return 0
        
        col_lock = self._get_collection_lock(collection)
        
        # Check if reload is needed (only if thread_safe)
        if self.thread_safe and self._needs_reload(collection):
            with col_lock.write_lock():
                if self._needs_reload(collection):
                    self._reload_collection(collection)
                return self._ensure_collection(collection).count()
        else:
            with col_lock.read_lock():
                return self._ensure_collection(collection).count()
    
    def persist_all(self):
        """Persist all collections."""
        if not os.path.exists(self.base_path):
            return
        
        if self.thread_safe and self._collections_lock:
            with self._collections_lock:
                collection_names = list(self.collections.keys())
        else:
            collection_names = list(self.collections.keys())
        
        for name in collection_names:
            try:
                self.persist(name)
            except Exception:
                pass
    
    def persist(self, collection: str = "default"):
        """Persist with optional thread/process safety."""
        if self.thread_safe and self._collections_lock:
            with self._collections_lock:
                if collection not in self.collections:
                    return
        else:
            if collection not in self.collections:
                return
        
        col_lock = self._get_collection_lock(collection)
        
        with col_lock.write_lock():
            gc.collect()
            self.collections[collection].persist()
            
            # Version tracking (only if thread_safe)
            if self.thread_safe:
                tracker = self._get_version_tracker(collection)
                tracker.increment_version()
                
                if self._collections_lock:
                    with self._collections_lock:
                        self.local_versions[collection] = tracker.get_version()
                else:
                    self.local_versions[collection] = tracker.get_version()
    
    def _maintenance_loop(self):
        """Background maintenance thread."""
        while not self.stop_maintenance:
            time.sleep(1)
            uptime = time.time() - self.start_time
            idle_time = time.time() - self.last_access_time
            
            if uptime > self.maintenance_interval and idle_time > self.idle_threshold:
                try:
                    self.persist_all()
                except Exception:
                    pass
                self.start_time = time.time()
    
    def vacuum(self, collection: str = "default"):
        """Vacuum with optional thread/process safety."""
        col_lock = self._get_collection_lock(collection)
        
        with col_lock.write_lock():
            # Reload if thread_safe
            if self.thread_safe and self._needs_reload(collection):
                self._reload_collection(collection)
            
            db = self._ensure_collection(collection)
            db.vacuum()
            
            # Version tracking (only if thread_safe)
            if self.thread_safe:
                tracker = self._get_version_tracker(collection)
                tracker.increment_version()
                
                if self._collections_lock:
                    with self._collections_lock:
                        self.local_versions[collection] = tracker.get_version()
                else:
                    self.local_versions[collection] = tracker.get_version()
    
    def close(self):
        """Gracefully close the database."""
        self.stop_maintenance = True
        if self.m_thread.is_alive():
            self.m_thread.join(timeout=5)
        self.persist_all()
