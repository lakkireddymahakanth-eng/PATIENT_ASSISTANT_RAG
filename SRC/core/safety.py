# src/core/safety.py

EMERGENCY_KEYWORDS = [
    "chest pain",
    "difficulty breathing",
    "severe bleeding",
    "unconscious"
]

def check_emergency(question: str) -> bool:
    q = question.lower()
    return any(k in q for k in EMERGENCY_KEYWORDS)