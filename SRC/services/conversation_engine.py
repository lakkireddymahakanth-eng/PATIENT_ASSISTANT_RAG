# ============================================================
# conversation_engine.py
# Chat booking with emergency detection
# ============================================================

import ollama
import json
from src.services.appointment_service import detect_emergency

REQUIRED_FIELDS = ["reason", "date", "time", "location"]


# ============================================================
# EXTRACT A SINGLE FIELD
# ============================================================
def extract_field(user_input, field_hint):
    examples = {
        "date":     '"tomorrow" or "25th March" or "next Monday"',
        "time":     '"10 AM" or "2:30 PM" or "morning"',
        "location": '"Berlin" or "Bangalore" or "London"',
    }

    prompt = f"""
Extract the field "{field_hint}" from this user message.
User said: "{user_input}"
Return ONLY valid JSON: {{"{field_hint}": "value"}}
If not found, return: {{}}
Examples for {field_hint}: {examples.get(field_hint, "")}
No explanation. No markdown. Only JSON.
"""
    try:
        response = ollama.chat(
            model="llama3",
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response["message"]["content"].strip()

        if "```" in raw:
            for part in raw.split("```"):
                part = part.strip().lstrip("json").strip()
                if part.startswith("{"):
                    raw = part
                    break

        start = raw.find("{")
        end   = raw.rfind("}") + 1
        if start != -1 and end > start:
            parsed = json.loads(raw[start:end])
            value  = parsed.get(field_hint, "")
            if isinstance(value, str):
                value = value.strip()
            bad = {"none", "null", "n/a", "not provided", "not mentioned", "unknown", ""}
            if value.lower() not in bad:
                return value
    except Exception as e:
        print(f"⚠️ Extraction error [{field_hint}]: {e}")
    return None


# ============================================================
# QUESTIONS
# ============================================================
FIELD_QUESTIONS = {
    "reason":   "Your record shows **{condition}**. Is that the reason for today's visit, or is there something else you'd like to address?",
    "date":     "What date would you like the appointment? For example, tomorrow or March 25th.",
    "time":     "What time works for you? For example, 10 AM or 2 in the afternoon.",
    "location": "Which city or area would you prefer for the appointment?",
}


# ============================================================
# GREETING
# ============================================================
def get_greeting(patient):
    name      = patient.get("name", "")
    condition = patient.get("condition", "")

    # Warn immediately if condition sounds like emergency
    if detect_emergency(condition):
        return (
            f"🚨 Hello {name}! Your condition **{condition}** sounds urgent. "
            f"I am flagging this as an **emergency** and will assign you a priority doctor immediately. "
            f"Which city are you in right now?"
        )

    return (
        f"Hello {name}! I can see you are registered with **{condition}**. "
        f"Is that the reason for today's visit, or is there something else you'd like to address?"
    )


# ============================================================
# PROCESS ONE CHAT MESSAGE
# ============================================================
def process_chat_message(user_input, details, patient, conversation_history):
    """
    Process one user message.
    Returns: (ai_response, updated_details, is_complete)
    """
    user_input = user_input.strip()

    # ── Check for emergency in user's message ───────────────
    if detect_emergency(user_input) and not details.get("emergency"):
        details["emergency"] = True
        print("🚨 Emergency detected in user message!")

    # ── Extract required fields ──────────────────────────────
    for field in REQUIRED_FIELDS:
        if not details.get(field):
            value = extract_field(user_input, field)
            if value:
                details[field] = value
                print(f"✅ Extracted {field}: {value}")

    missing = [f for f in REQUIRED_FIELDS if not details.get(f)]

    # ── Emergency shortcut — only need location ──────────────
    if details.get("emergency"):
        # For emergencies, skip date/time — book immediately
        if details.get("location"):
            response = (
                "🚨 **Emergency detected!** I am booking you with an **emergency doctor immediately**. "
                "Please proceed to the clinic or call emergency services if needed. Please wait..."
            )
            # Mark date/time as now so booking proceeds
            now = __import__("datetime").datetime.now()
            details["date"] = now.strftime("%d %B")
            details["time"] = now.strftime("%H:%M")
            return response, details, True
        else:
            return (
                "🚨 This sounds like an **emergency**! "
                "Which city are you in? I will book you with an emergency doctor right away.",
                details, False
            )

    # ── Normal flow — all fields collected ───────────────────
    if not missing:
        date = details.get("date", "")
        time = details.get("time", "")
        loc  = details.get("location", "")
        response = (
            f"Perfect! I have everything I need. "
            f"Booking your appointment for **{date}** at **{time}** in **{loc}**. "
            f"Please wait a moment..."
        )
        return response, details, True

    # ── Ask for next missing field ───────────────────────────
    next_field   = missing[0]
    next_question = FIELD_QUESTIONS[next_field]
    return next_question, details, False


# ============================================================
# TERMINAL VERSION (for testing)
# ============================================================
def run_conversation_loop(patient_id, patient):
    from src.services.location_service import get_location_details
    from src.services.appointment_service import book_appointment
    from src.services.conversation_history_service import save_conversation

    allergies = patient.get("allergies", [])
    allergy_str = ', '.join(allergies) if isinstance(allergies, list) else str(allergies)

    details = {
        "name":      patient.get("name", ""),
        "phone":     patient.get("phone", ""),
        "problem":   None,   # collected fresh via "reason" question
        "notes":     f"Allergies: {allergy_str}",
        "emergency": detect_emergency(patient.get("condition", "")),
        "reason":    None,
        "date":      None,
        "time":      None,
        "location":  None,
    }

    conversation_history = []
    print(f"\n🤖 AI: {get_greeting(patient)}")

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue

        conversation_history.append({"role": "user", "content": user_input})

        ai_response, details, is_complete = process_chat_message(
            user_input, details, patient, conversation_history
        )

        print(f"🤖 AI: {ai_response}")
        conversation_history.append({"role": "assistant", "content": ai_response})

        if is_complete:
            location_data = get_location_details(details["location"])
            if not location_data:
                print("🤖 AI: Sorry, I couldn't find that location. Please try again.")
                details["location"] = None
                continue

            appointment = book_appointment(
                patient_id, patient, location_data,
                patient.get("insurance", "none"), details
            )
            save_conversation(patient_id, conversation_history)
            print(f"\n✅ Appointment booked! ID: {appointment['appointment_id']}")
            print(f"   Priority : {appointment['priority']}")
            print(f"   Doctor   : {appointment['doctor']}")
            print(f"   Slot     : {appointment['datetime']}")
            return appointment, conversation_history

    return None, conversation_history