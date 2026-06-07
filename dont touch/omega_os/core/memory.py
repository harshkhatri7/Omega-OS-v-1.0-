import os
import json
import base64

MEMORY_DIR = "localSaved"
MEMORY_FILE = os.path.join(MEMORY_DIR, "memory.dat")

def _init_memory():
    if not os.path.exists(MEMORY_DIR):
        os.makedirs(MEMORY_DIR)
    if not os.path.exists(MEMORY_FILE):
        _save_raw({})

def _load_raw() -> dict:
    _init_memory()
    try:
        with open(MEMORY_FILE, "r") as f:
            encoded_data = f.read()
            if not encoded_data: return {}
            decoded_bytes = base64.b64decode(encoded_data.encode('utf-8'))
            return json.loads(decoded_bytes.decode('utf-8'))
    except Exception:
        return {}

def _save_raw(data: dict):
    _init_memory()
    json_str = json.dumps(data)
    encoded_bytes = base64.b64encode(json_str.encode('utf-8'))
    with open(MEMORY_FILE, "w") as f:
        f.write(encoded_bytes.decode('utf-8'))

def save_fact(key: str, value: str):
    """Saves a fact into the Base64 encrypted local storage."""
    data = _load_raw()
    data[key] = value
    _save_raw(data)

def get_fact(key: str) -> str:
    """Retrieves a fact from local storage."""
    data = _load_raw()
    return data.get(key, "")
