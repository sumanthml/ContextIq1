import os
import json
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
os.makedirs(DATA_DIR, exist_ok=True)

USERS_FILE = os.path.join(DATA_DIR, "users.json")
USER_FILES_FILE = os.path.join(DATA_DIR, "user_files.json")
CHAT_MESSAGES_FILE = os.path.join(DATA_DIR, "chat_messages.json")

def _load_json(file_path: str, default: Any) -> Any:
    if not os.path.exists(file_path):
        return default
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Error reading {file_path}: {e}")
        return default

def _save_json(file_path: str, data: Any) -> None:
    try:
        temp_path = f"{file_path}.tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, file_path)
    except Exception as e:
        print(f"❌ Error writing to {file_path}: {e}")

# --- USER ACCOUNTS DATABASE ---
def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    users = _load_json(USERS_FILE, [])
    for u in users:
        if u.get("email", "").lower() == email.lower().strip():
            return u
    return None

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    users = _load_json(USERS_FILE, [])
    for u in users:
        if u.get("id") == user_id:
            return u
    return None

def save_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    users = _load_json(USERS_FILE, [])
    # Update existing or add new
    existing_idx = next((i for i, u in enumerate(users) if u.get("id") == user_data.get("id")), -1)
    if existing_idx >= 0:
        users[existing_idx] = user_data
    else:
        users.append(user_data)
    _save_json(USERS_FILE, users)
    return user_data

# --- USER FILES DATABASE ---
def get_user_files(user_id: str) -> List[Dict[str, Any]]:
    files = _load_json(USER_FILES_FILE, [])
    return [f for f in files if f.get("user_id") == user_id]

def save_user_file(user_id: str, file_name: str, file_size: int) -> Dict[str, Any]:
    files = _load_json(USER_FILES_FILE, [])
    existing = next((f for f in files if f.get("user_id") == user_id and f.get("file_name") == file_name), None)
    now_str = datetime.utcnow().isoformat() + "Z"
    if existing:
        existing["file_size"] = file_size
        existing["updated_at"] = now_str
        _save_json(USER_FILES_FILE, files)
        return existing
    else:
        new_file = {
            "id": f"file_{uuid.uuid4().hex[:10]}",
            "user_id": user_id,
            "file_name": file_name,
            "file_size": file_size,
            "created_at": now_str
        }
        files.append(new_file)
        _save_json(USER_FILES_FILE, files)
        return new_file

# --- CHAT MESSAGES DATABASE ---
def get_chat_history(user_id: str, file_name: str) -> List[Dict[str, Any]]:
    msgs = _load_json(CHAT_MESSAGES_FILE, [])
    filtered = [
        {"role": m.get("role"), "content": m.get("content"), "created_at": m.get("created_at")}
        for m in msgs
        if m.get("user_id") == user_id and m.get("file_name") == file_name
    ]
    return sorted(filtered, key=lambda x: x.get("created_at", ""))

def save_chat_message(user_id: str, file_name: str, role: str, content: str) -> Dict[str, Any]:
    msgs = _load_json(CHAT_MESSAGES_FILE, [])
    new_msg = {
        "id": f"msg_{uuid.uuid4().hex[:10]}",
        "user_id": user_id,
        "file_name": file_name,
        "role": role,
        "content": content,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    msgs.append(new_msg)
    _save_json(CHAT_MESSAGES_FILE, msgs)
    return new_msg
