# core/app_state.py
"""App state - global state management"""
import threading
from typing import Optional

_state_lock = threading.RLock()
_state: dict = {
    "presence": {},
    "sensor_readings": {},
    "climate": {},
    "device_states": {},
}


def get_state() -> dict:
    with _state_lock:
        return _state.copy()


def get_nodes_copy() -> dict:
    """Get current device states for memory snapshot"""
    with _state_lock:
        return _state.copy()


def update_state(new_state: dict):
    with _state_lock:
        _state.update(new_state)


def update_device_state(entity_id: str, state: dict):
    with _state_lock:
        if "device_states" not in _state:
            _state["device_states"] = {}
        _state["device_states"][entity_id] = state
