from __future__ import annotations
from threading import RLock
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import json
import os
import tempfile

from core.schemas import TradingState, ExecutedTrade
from utils.logger import log_info, log_error

MEMORY_PATH = os.path.join("state", "memory.json")


class SharedState:
    """
    🌍 Unified Global SharedState — Production Grade
    ------------------------------------------------------------
    Combines caching, persistent user sessions, and global memory
    for all AI trading agents and LangGraph nodes.
    """

    _instance: Optional["SharedState"] = None
    _lock = RLock()

    def __init__(self, memory_file: str = MEMORY_PATH):
        self._memory_file = memory_file
        self._state: Dict[str, Any] = {
            "sessions": {},        # user_id → TradingState
            "global_context": {},  # global memory / cache
            "last_updated": datetime.utcnow(),
        }

        try:
            disk = self._load_from_disk_raw()
            self._restore_from_disk(disk)
            log_info("[SharedState] ✅ Loaded from disk successfully.")
        except Exception as e:
            log_error(f"[SharedState] ⚠️ Disk restore failed: {e}")
            pass

    # --------------------------------------------------------
    # Singleton Accessor
    # --------------------------------------------------------
    @classmethod
    def get_instance(cls) -> "SharedState":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    # --------------------------------------------------------
    # Disk IO Helpers
    # --------------------------------------------------------
    def _ensure_dir(self):
        os.makedirs(os.path.dirname(self._memory_file) or ".", exist_ok=True)

    def _load_from_disk_raw(self) -> Dict[str, Any]:
        """Safely load memory.json from disk."""
        if not os.path.exists(self._memory_file):
            self._ensure_dir()
            baseline = {"sessions": {}, "global_context": {}, "last_updated": None}
            with open(self._memory_file, "w", encoding="utf-8") as f:
                json.dump(baseline, f, indent=4)
            return baseline
        try:
            with open(self._memory_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            corrupt_path = f"{self._memory_file}.corrupt.{int(datetime.utcnow().timestamp())}"
            try:
                os.rename(self._memory_file, corrupt_path)
            except Exception:
                pass
            log_error(f"[SharedState] ⚠️ Corrupt memory.json backed up as {corrupt_path}")
            return {"sessions": {}, "global_context": {}, "last_updated": None}

    def _save_to_disk_raw(self, data: Dict[str, Any]):
        """Atomic save to memory.json."""
        try:
            self._ensure_dir()
            dirpath = os.path.dirname(self._memory_file) or "."
            fd, tmp_path = tempfile.mkstemp(dir=dirpath, prefix="memory_", suffix=".json")
            with os.fdopen(fd, "w", encoding="utf-8") as tmpf:
                json.dump(data, tmpf, indent=4, default=str)
                tmpf.flush()
                os.fsync(tmpf.fileno())
            os.replace(tmp_path, self._memory_file)
        except Exception as e:
            log_error(f"[SharedState] ❌ Failed to save memory: {e}")

    # --------------------------------------------------------
    # Internal State Management
    # --------------------------------------------------------
    def _restore_from_disk(self, disk: Dict[str, Any]):
        """Rehydrate TradingState objects from disk JSON."""
        sessions = disk.get("sessions", {}) or {}
        restored_sessions: Dict[str, TradingState] = {}
        for user_id, raw in sessions.items():
            try:
                restored_sessions[user_id] = TradingState.model_validate(raw)
            except Exception:
                restored_sessions[user_id] = TradingState(symbol="")

        self._state["sessions"] = restored_sessions
        self._state["global_context"] = disk.get("global_context", {}) or {}
        last = disk.get("last_updated")
        try:
            self._state["last_updated"] = datetime.fromisoformat(last) if last else datetime.utcnow()
        except Exception:
            self._state["last_updated"] = datetime.utcnow()

    def _serialize_for_disk(self) -> Dict[str, Any]:
        """Serialize in-memory state for disk persistence."""
        serial_sessions: Dict[str, Any] = {}
        for uid, state_obj in self._state.get("sessions", {}).items():
            try:
                if isinstance(state_obj, TradingState):
                    serial_sessions[uid] = state_obj.model_dump()
                elif hasattr(state_obj, "dict"):
                    serial_sessions[uid] = state_obj.dict()
                else:
                    serial_sessions[uid] = dict(state_obj)
            except Exception:
                serial_sessions[uid] = {"symbol": getattr(state_obj, "symbol", ""), "note": "serialization_failed"}

        return {
            "sessions": serial_sessions,
            "global_context": self._state.get("global_context", {}),
            "last_updated": datetime.utcnow().isoformat(),
        }

    # --------------------------------------------------------
    # 🔑 Modern API (User & Global)
    # --------------------------------------------------------
    def get_user_state(self, user_id: str) -> TradingState:
        """Return or create a user session TradingState."""
        with self._lock:
            sessions = self._state.setdefault("sessions", {})
            if user_id not in sessions:
                sessions[user_id] = TradingState(symbol="")
                self._save_to_disk()
            return sessions[user_id]

    def update_user_state(self, user_id: str, key: str, value: Any):
        """Update field for a user's TradingState."""
        with self._lock:
            state = self.get_user_state(user_id)
            try:
                setattr(state, key, value)
            except Exception:
                data = state.model_dump()
                data[key] = value
                self._state["sessions"][user_id] = TradingState.model_validate(data)
            self._state["last_updated"] = datetime.utcnow()
            self._save_to_disk()

    def set_global(self, key: str, value: Any):
        """Set global variable or cached data."""
        with self._lock:
            self._state.setdefault("global_context", {})[key] = value
            self._state["last_updated"] = datetime.utcnow()
            self._save_to_disk()

    def get_global(self, key: str, default: Any = None) -> Any:
        """Fetch global context value."""
        with self._lock:
            return self._state.get("global_context", {}).get(key, default)

    # --------------------------------------------------------
    # 🧠 Cache API (compatible with data_collector_agent)
    # --------------------------------------------------------
    def get(self, key: str) -> Optional[Any]:
        """Global key-value cache retrieval."""
        return self.get_global(key)

    def set(self, key: str, value: Any):
        """Global key-value cache storage."""
        self.set_global(key, value)

    def delete(self, key: str):
        """Delete a key from global context."""
        with self._lock:
            if key in self._state.get("global_context", {}):
                del self._state["global_context"][key]
                self._save_to_disk()

    # --------------------------------------------------------
    # 💹 Trade Record Management
    # --------------------------------------------------------
    def record_trade(self, user_id: str, trade: ExecutedTrade):
        """Append an executed trade to user trade history."""
        with self._lock:
            state = self.get_user_state(user_id)
            if not hasattr(state, "trade_history") or state.trade_history is None:
                state.trade_history = []
            state.trade_history.append(trade)
            self._state["last_updated"] = datetime.utcnow()
            self._save_to_disk()

    # --------------------------------------------------------
    # 🧾 Utility / Maintenance
    # --------------------------------------------------------
    def export(self) -> Dict[str, Any]:
        """Export full serializable memory snapshot."""
        with self._lock:
            return self._serialize_for_disk()

    def clear_all(self):
        """Completely reset shared memory."""
        with self._lock:
            self._state = {"sessions": {}, "global_context": {}, "last_updated": datetime.utcnow()}
            self._save_to_disk()
            log_info("[SharedState] 🧹 Cleared all cached memory.")

    def _save_to_disk(self):
        """Public wrapper for atomic save."""
        payload = self._serialize_for_disk()
        self._save_to_disk_raw(payload)


# --------------------------------------------------------
# Singleton + Legacy API
# --------------------------------------------------------
shared_state = SharedState.get_instance()


def load_memory() -> dict:
    """Legacy alias for older modules."""
    return shared_state._load_from_disk_raw()


def save_memory() -> None:
    """Legacy alias for older modules."""
    shared_state._save_to_disk()
