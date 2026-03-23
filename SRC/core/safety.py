# src/core/safety.py

EMERGENCY_KEYWORDS = [
    "chest pain", "difficulty breathing", "shortness of breath",
    "severe bleeding", "unconscious", "heart attack", "stroke",
    "fainting", "seizure", "can't breathe", "tight chest"
]

HIGH_RISK_KEYWORDS = [
    "severe pain", "high fever", "vomiting blood",
    "black stool", "persistent cough", "vision loss"
]


def check_emergency(question: str) -> bool:
    q = question.lower()
    return any(k in q for k in EMERGENCY_KEYWORDS)


def check_high_risk(question: str) -> bool:
    q = question.lower()
    return any(k in q for k in HIGH_RISK_KEYWORDS)


def safe_fallback():
    return (
        "⚠️ I'm not fully confident about this. "
        "Please consult a qualified doctor for proper medical advice."
    )


def emergency_response():
    return (
        "🚨 This may be a medical emergency.\n\n"
        "Please seek immediate medical attention or call emergency services."
    )