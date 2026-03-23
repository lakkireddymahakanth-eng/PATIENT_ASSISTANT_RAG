import json
import os
from datetime import datetime

FILE = "data/medical_history.json"


def log_event(patient_id, event):

    history = []

    if os.path.exists(FILE):
        with open(FILE, "r") as f:
            history = json.load(f)

    history.append({
        "patient_id": patient_id,
        "event": event,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

    with open(FILE, "w") as f:
        json.dump(history, f, indent=2)