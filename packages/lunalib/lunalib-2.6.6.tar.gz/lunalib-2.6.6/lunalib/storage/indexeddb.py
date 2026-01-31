import sys
import json
import base64
import pickle
from typing import Any, Dict, Iterable, Optional, List

try:
    from pyodide.ffi import create_proxy, to_py, run_sync
    import js  # type: ignore
    _PYODIDE_AVAILABLE = True
except Exception:
    create_proxy = None
    to_py = None
    run_sync = None
    js = None
    _PYODIDE_AVAILABLE = False


class IndexedDBStore:
    """Minimal IndexedDB wrapper for Pyodide/Web builds."""

    def __init__(self, db_name: str, stores: Iterable[str]):
        self.db_name = db_name
        self.stores = list(stores)
        self._db = None
        self._memory_fallback: Dict[str, Dict[str, Any]] = {
            name: {} for name in self.stores
        }
        self._use_memory = sys.platform != "emscripten" or not _PYODIDE_AVAILABLE or run_sync is None

    def _await(self, coro):
        if run_sync is None:
            raise RuntimeError("Pyodide run_sync not available")
        return run_sync(coro)

    def _ensure_db(self):
        if self._use_memory:
            return None
        if self._db is not None:
            return self._db

        async def _open_db():
            import asyncio

            loop = asyncio.get_event_loop()
            future = loop.create_future()

            def on_success(event):
                future.set_result(event.target.result)

            def on_error(event):
                future.set_exception(RuntimeError(str(event.target.error)))

            def on_upgrade(event):
                db = event.target.result
                for store in self.stores:
                    if not db.objectStoreNames.contains(store):
                        db.createObjectStore(store)

            request = js.indexedDB.open(self.db_name, 1)
            request.onupgradeneeded = create_proxy(on_upgrade)
            request.onsuccess = create_proxy(on_success)
            request.onerror = create_proxy(on_error)

            return await future

        try:
            self._db = self._await(_open_db())
        except Exception:
            self._use_memory = True
            return None
        return self._db

    def _serialize(self, value: Any) -> str:
        if isinstance(value, (bytes, bytearray)):
            return base64.b64encode(bytes(value)).decode("utf-8")
        try:
            return json.dumps(value)
        except Exception:
            payload = pickle.dumps(value)
            return base64.b64encode(payload).decode("utf-8")

    def _deserialize(self, value: Optional[str]) -> Any:
        if value is None:
            return None
        try:
            return json.loads(value)
        except Exception:
            try:
                raw = base64.b64decode(value.encode("utf-8"))
                try:
                    return pickle.loads(raw)
                except Exception:
                    return raw
            except Exception:
                return value

    def get(self, store: str, key: str) -> Any:
        if self._use_memory:
            return self._memory_fallback.get(store, {}).get(key)

        db = self._ensure_db()
        if db is None:
            return None

        async def _get():
            import asyncio

            loop = asyncio.get_event_loop()
            future = loop.create_future()
            tx = db.transaction(store, "readonly")
            obj = tx.objectStore(store)
            req = obj.get(key)

            def on_success(event):
                future.set_result(event.target.result)

            def on_error(event):
                future.set_exception(RuntimeError(str(event.target.error)))

            req.onsuccess = create_proxy(on_success)
            req.onerror = create_proxy(on_error)
            return await future

        try:
            result = self._await(_get())
            return self._deserialize(result)
        except Exception:
            return None

    def put(self, store: str, key: str, value: Any) -> bool:
        if self._use_memory:
            self._memory_fallback.setdefault(store, {})[key] = value
            return True

        db = self._ensure_db()
        if db is None:
            return False

        async def _put():
            import asyncio

            loop = asyncio.get_event_loop()
            future = loop.create_future()
            tx = db.transaction(store, "readwrite")
            obj = tx.objectStore(store)
            req = obj.put(self._serialize(value), key)

            def on_success(event):
                future.set_result(True)

            def on_error(event):
                future.set_exception(RuntimeError(str(event.target.error)))

            req.onsuccess = create_proxy(on_success)
            req.onerror = create_proxy(on_error)
            return await future

        try:
            self._await(_put())
            return True
        except Exception:
            return False

    def delete(self, store: str, key: str) -> bool:
        if self._use_memory:
            self._memory_fallback.get(store, {}).pop(key, None)
            return True

        db = self._ensure_db()
        if db is None:
            return False

        async def _delete():
            import asyncio

            loop = asyncio.get_event_loop()
            future = loop.create_future()
            tx = db.transaction(store, "readwrite")
            obj = tx.objectStore(store)
            req = obj.delete(key)

            def on_success(event):
                future.set_result(True)

            def on_error(event):
                future.set_exception(RuntimeError(str(event.target.error)))

            req.onsuccess = create_proxy(on_success)
            req.onerror = create_proxy(on_error)
            return await future

        try:
            self._await(_delete())
            return True
        except Exception:
            return False

    def get_all_items(self, store: str) -> List[Dict[str, Any]]:
        if self._use_memory:
            return [
                {"key": key, "value": value}
                for key, value in self._memory_fallback.get(store, {}).items()
            ]

        db = self._ensure_db()
        if db is None:
            return []

        async def _get_all():
            import asyncio

            loop = asyncio.get_event_loop()
            future = loop.create_future()
            tx = db.transaction(store, "readonly")
            obj = tx.objectStore(store)
            req = obj.getAllKeys()

            def on_success(event):
                keys = list(event.target.result)
                future.set_result(keys)

            def on_error(event):
                future.set_exception(RuntimeError(str(event.target.error)))

            req.onsuccess = create_proxy(on_success)
            req.onerror = create_proxy(on_error)
            keys = await future
            items = []
            for key in keys:
                value = await self._get_one(obj, key)
                items.append({"key": key, "value": value})
            return items

        try:
            return self._await(_get_all())
        except Exception:
            return []

    async def _get_one(self, obj, key):
        import asyncio

        loop = asyncio.get_event_loop()
        future = loop.create_future()
        req = obj.get(key)

        def on_success(event):
            future.set_result(event.target.result)

        def on_error(event):
            future.set_exception(RuntimeError(str(event.target.error)))

        req.onsuccess = create_proxy(on_success)
        req.onerror = create_proxy(on_error)
        result = await future
        return self._deserialize(result)
