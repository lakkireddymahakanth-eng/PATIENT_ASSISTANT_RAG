# ============================================================
# appointment_service.py
# Handles booking with doctor schedules + emergency detection
# ============================================================

import json
import os
import random
from datetime import datetime, timedelta

APPOINTMENT_FILE = "data/appointments.json"

# ============================================================
# DOCTOR REGISTRY WITH WORKING HOURS & MAX SLOTS PER DAY
# ============================================================
DOCTORS = {
    "cardiologist": [
        {"name": "Dr. Heart",  "hours": (9, 17),  "days": [0,1,2,3,4],    "slot_duration": 30, "max_per_day": 8},
        {"name": "Dr. Pulse",  "hours": (10, 18), "days": [1,2,3,4,5],    "slot_duration": 30, "max_per_day": 6},
    ],
    "general": [
        {"name": "Dr. Smith",  "hours": (8, 16),  "days": [0,1,2,3,4],    "slot_duration": 20, "max_per_day": 12},
        {"name": "Dr. Kumar",  "hours": (12, 20), "days": [0,1,2,3,4,5],  "slot_duration": 20, "max_per_day": 10},
    ],
    "dermatologist": [
        {"name": "Dr. Skin",   "hours": (9, 15),  "days": [1,3,5],        "slot_duration": 30, "max_per_day": 6},
    ],
    "neurologist": [
        {"name": "Dr. Brain",  "hours": (10, 16), "days": [0,2,4],        "slot_duration": 45, "max_per_day": 5},
    ],
}

# Emergency doctors available 24/7
EMERGENCY_DOCTORS = [
    {"name": "Dr. Emergency",  "hours": (0, 24), "days": [0,1,2,3,4,5,6], "slot_duration": 15, "max_per_day": 99},
    {"name": "Dr. Urgent Care","hours": (0, 24), "days": [0,1,2,3,4,5,6], "slot_duration": 15, "max_per_day": 99},
]

# ============================================================
# EMERGENCY KEYWORDS
# ============================================================
EMERGENCY_KEYWORDS = [
    "chest pain", "heart attack", "can't breathe", "cannot breathe",
    "difficulty breathing", "stroke", "unconscious", "fainted", "fainting",
    "severe bleeding", "heavy bleeding", "overdose", "seizure", "convulsion",
    "severe pain", "unbearable pain", "extreme pain", "anaphylaxis", "allergic reaction",
    "broken bone", "fracture", "head injury", "loss of vision", "sudden blindness",
    "paralysis", "numb", "high fever", "fever above 104", "suicidal",
    "can't move", "cannot move", "choking", "vomiting blood", "coughing blood",
    "urgent", "emergency", "critical", "dying", "severe"
]

def detect_emergency(problem_text):
    """Returns True if the problem sounds like an emergency."""
    if not problem_text:
        return False
    text = problem_text.lower()
    return any(keyword in text for keyword in EMERGENCY_KEYWORDS)



# ============================================================
# DISPATCH AMBULANCE
# ============================================================
def dispatch_ambulance(patient_name, location_city, lat_lng, patient_condition):
    """
    Dispatches ambulance and logs to data/ambulance_dispatch.json.
    In production: replace with real emergency services API.
    """
    import json, os
    from datetime import datetime

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    record = {
        "dispatched_at":   now,
        "patient_name":    patient_name,
        "condition":       patient_condition,
        "location_city":   location_city,
        "coordinates":     lat_lng,
        "status":          "AMBULANCE DISPATCHED",
        "eta_minutes":     8,
    }

    log_file = "data/ambulance_dispatch.json"
    os.makedirs("data", exist_ok=True)
    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file) as f:
                content_log = f.read().strip()
                if content_log:
                    logs = json.loads(content_log)
        except Exception:
            pass
    logs.append(record)
    with open(log_file, "w") as f:
        json.dump(logs, f, indent=2)

    print(f"\n🚑 AMBULANCE DISPATCHED → {location_city} | ETA: ~8 mins")
    print(f"   Patient  : {patient_name}")
    print(f"   Condition: {patient_condition}")
    return record

# ============================================================
# SPECIALIZATION DETECTION
# ============================================================
def get_specialization(condition):
    if not condition:
        return "general"
    condition = condition.lower()
    if any(w in condition for w in ["heart", "chest", "cardiac", "hypertension", "blood pressure", "pulse"]):
        return "cardiologist"
    elif any(w in condition for w in ["skin", "rash", "itch", "acne", "derma"]):
        return "dermatologist"
    elif any(w in condition for w in ["headache", "migraine", "brain", "neuro", "dizzy", "seizure", "convulsion"]):
        return "neurologist"
    else:
        return "general"


# ============================================================
# LOAD / SAVE
# ============================================================
def load_appointments():
    if not os.path.exists(APPOINTMENT_FILE):
        os.makedirs(os.path.dirname(APPOINTMENT_FILE), exist_ok=True)
        return []
    try:
        with open(APPOINTMENT_FILE, "r") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"⚠️  appointments.json corrupt: {e}. Starting fresh.")
        os.rename(APPOINTMENT_FILE, APPOINTMENT_FILE + ".backup")
        return []


def save_appointments(data):
    os.makedirs(os.path.dirname(APPOINTMENT_FILE), exist_ok=True)
    with open(APPOINTMENT_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ============================================================
# COUNT EXISTING BOOKINGS FOR A DOCTOR ON A DATE
# ============================================================
def count_bookings(doctor_name, date_str):
    appointments = load_appointments()
    return sum(
        1 for a in appointments
        if a.get("doctor") == doctor_name
        and a.get("datetime", "").startswith(date_str)
        and a.get("status") != "cancelled"
    )


# ============================================================
# GENERATE AVAILABLE SLOTS FOR A DOCTOR
# ============================================================
def get_available_slots(doctor_info, target_date=None):
    """
    Returns list of available datetime strings for a doctor.
    target_date: datetime object. If None, checks next 5 working days.
    """
    slots = []
    start_hour, end_hour = doctor_info["hours"]
    working_days         = doctor_info["days"]
    slot_mins            = doctor_info["slot_duration"]
    max_per_day          = doctor_info["max_per_day"]

    check_dates = [target_date] if target_date else [
        datetime.now() + timedelta(days=i) for i in range(1, 8)
    ]

    for day in check_dates:
        if day.weekday() not in working_days:
            continue

        date_str     = day.strftime("%Y-%m-%d")
        booked_count = count_bookings(doctor_info["name"], date_str)

        if booked_count >= max_per_day:
            continue  # Doctor fully booked this day

        # Generate time slots within working hours
        current = day.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        end_dt  = day.replace(hour=min(end_hour, 23), minute=0, second=0, microsecond=0)

        while current < end_dt:
            slots.append(current.strftime("%Y-%m-%d %H:%M"))
            current += timedelta(minutes=slot_mins)

        if slots:
            break  # Return slots for first available day

    return slots


# ============================================================
# FIND BEST AVAILABLE DOCTOR + SLOT
# ============================================================
def find_available_doctor(specialization, is_emergency, preferred_date=None, preferred_time=None):
    """
    Finds an available doctor and returns (doctor_name, slot).
    Emergency patients get immediate emergency doctors.
    """

    # Emergency → always use emergency doctor
    if is_emergency:
        doc_info = random.choice(EMERGENCY_DOCTORS)
        now_slot = datetime.now().strftime("%Y-%m-%d %H:%M")
        print(f"🚨 Emergency booking → {doc_info['name']} at {now_slot}")
        return doc_info["name"], now_slot, True

    doctor_list = DOCTORS.get(specialization, DOCTORS["general"])

    # Parse preferred date if given
    target_date = None
    if preferred_date and preferred_date not in ("not provided", "none", ""):
        for fmt in ["%d %B", "%B %d", "%d %B %Y", "%Y-%m-%d", "%dth %B", "%dst %B", "%dnd %B", "%drd %B"]:
            try:
                parsed = datetime.strptime(preferred_date, fmt)
                target_date = parsed.replace(year=datetime.now().year)
                break
            except ValueError:
                continue

    # Try each doctor
    for doc_info in doctor_list:
        slots = get_available_slots(doc_info, target_date)

        if not slots:
            continue

        # If user has a preferred time, find closest slot
        chosen_slot = slots[0]
        if preferred_time and preferred_time not in ("not provided", "none", ""):
            chosen_slot = match_preferred_time(slots, preferred_time)

        print(f"✅ Doctor found: {doc_info['name']} → slot: {chosen_slot}")
        return doc_info["name"], chosen_slot, False

    # All doctors full → fallback to next available
    print("⚠️  All preferred doctors full, using fallback slot")
    fallback_doc = doctor_list[0]
    fallback_slot = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d 10:00")
    return fallback_doc["name"], fallback_slot, False


def match_preferred_time(slots, preferred_time):
    """Find the slot closest to the user's preferred time."""
    import re
    preferred_time = preferred_time.lower().strip()

    # Spoken word → hour range
    time_map = {
        "morning":   range(8, 12),
        "afternoon": range(12, 17),
        "evening":   range(17, 21),
        "night":     range(20, 24),
    }
    for label, hour_range in time_map.items():
        if label in preferred_time:
            for slot in slots:
                hour = int(slot.split(" ")[1].split(":")[0])
                if hour in hour_range:
                    return slot

    # Parse exact time: "12:00 PM", "10:30 AM", "14:00", "12pm", "10am"
    preferred_hour   = None
    preferred_minute = 0
    try:
        for fmt in ["%I:%M %p", "%I %p", "%H:%M", "%H"]:
            try:
                t = datetime.strptime(preferred_time.upper(), fmt)
                preferred_hour   = t.hour
                preferred_minute = t.minute
                break
            except ValueError:
                continue

        if preferred_hour is None:
            m = re.match(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", preferred_time)
            if m:
                h  = int(m.group(1))
                mn = int(m.group(2)) if m.group(2) else 0
                period = m.group(3)
                if period == "pm" and h != 12:
                    h += 12
                elif period == "am" and h == 12:
                    h = 0
                preferred_hour   = h
                preferred_minute = mn
    except Exception:
        pass

    # Find closest slot to preferred hour:minute
    if preferred_hour is not None:
        best_slot = None
        best_diff = float("inf")
        for slot in slots:
            parts     = slot.split(" ")[1].split(":")
            slot_hour = int(parts[0])
            slot_min  = int(parts[1]) if len(parts) > 1 else 0
            diff = abs((slot_hour * 60 + slot_min) - (preferred_hour * 60 + preferred_minute))
            if diff < best_diff:
                best_diff = diff
                best_slot = slot
        if best_slot:
            return best_slot

    return slots[0]


# ============================================================
# MAIN BOOK APPOINTMENT FUNCTION
# ============================================================
def book_appointment(patient_id, patient, location_data, insurance, user_details):

    condition      = user_details.get("problem") or patient.get("condition", "general")
    specialization = get_specialization(condition)

    # ── Detect emergency ────────────────────────────────────
    is_emergency = (
        user_details.get("emergency", False) or
        detect_emergency(condition) or
        detect_emergency(user_details.get("notes", ""))
    )

    print(f"🏥 Specialization: {specialization} | Emergency: {is_emergency}")

    # ── Find available doctor + slot ────────────────────────
    doctor_name, slot, emergency_assigned = find_available_doctor(
        specialization=specialization,
        is_emergency=is_emergency,
        preferred_date=user_details.get("date", ""),
        preferred_time=user_details.get("time", ""),
    )

    appointment = {
        "appointment_id": f"A{random.randint(1000, 9999)}",
        "patient_id":     patient_id,

        # Patient info
        "name":           user_details.get("name")  or patient.get("name", "not provided"),
        "phone":          user_details.get("phone") or patient.get("phone", "not provided"),

        # Medical
        "problem":        condition,
        "notes":          user_details.get("notes", ""),
        "specialization": "emergency" if emergency_assigned else specialization,

        # Doctor & slot
        "doctor":         doctor_name,
        "datetime":       slot,

        # Emergency flag
        "emergency":      is_emergency,
        "priority":       "🚨 EMERGENCY" if is_emergency else "📅 NORMAL",

        # Location
        "location": {
            "address": location_data.get("full_address", ""),
            "city":    location_data.get("city", user_details.get("location", "")),
            "country": location_data.get("country", ""),
        },

        "insurance": {"type": insurance or "not provided"},
        "status":    "booked",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    appointments = load_appointments()
    appointments.append(appointment)
    save_appointments(appointments)

    print(f"✅  Appointment saved: {appointment['appointment_id']} | Priority: {appointment['priority']}")
    return appointment