import json
from pathlib import Path

STATE_FILE = Path(".sync_state.json")

def load_state():
    if not STATE_FILE.exists():
        return {}
    return json.loads(STATE_FILE.read_text())

def save_state(state: dict):
    def default_serializer(obj):
        from uuid import UUID
        if isinstance(obj, UUID):
            return str(obj)
        raise TypeError(f"Type {type(obj)} not serializable")

    STATE_FILE.write_text(json.dumps(state, indent=2, default=default_serializer))
