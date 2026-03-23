# ============================================================
# conversation_history.py
# Save and load chat conversation history
# ============================================================

import json
import os
from datetime import datetime

FILE = "data/conversations.json"


def load_history():
    if not os.path.exists(FILE):
        os.makedirs(os.path.dirname(FILE), exist_ok=True)
        return []
    try:
        with open(FILE, "r") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"⚠️ conversations.json corrupt: {e}. Starting fresh.")
        os.rename(FILE, FILE + ".backup")
        return []


def save_conversation(patient_id, conversation):
    history = load_history()
    history.append({
        "patient_id":   patient_id,
        "conversation": conversation,
        "timestamp":    datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    os.makedirs(os.path.dirname(FILE), exist_ok=True)
    with open(FILE, "w") as f:
        json.dump(history, f, indent=2)