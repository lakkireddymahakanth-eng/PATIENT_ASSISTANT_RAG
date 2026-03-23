# ============================================================
# ai_voice_call.py
# AI Voice Appointment Booking with Emergency Flow
#
# INSTALL:
#   pip install openai-whisper sounddevice numpy scipy
#   pip install ollama edge-tts pygame requests geocoder
# ============================================================

import whisper
import sounddevice as sd
import numpy as np
import ollama
import json
import tempfile
import time
import asyncio
import os
import scipy.io.wavfile as wav
import edge_tts
import pygame
from datetime import datetime

from src.services.location_service import get_location_details
from src.services.appointment_service import book_appointment, detect_emergency


# ============================================================
# LOAD WHISPER MODEL
# ============================================================
print("⏳ Loading Whisper model...")
model = whisper.load_model("base")
print("✅ Whisper model loaded.")

pygame.mixer.init()


# ============================================================
# SPEAK
# ============================================================
def speak(text):
    print(f"\n🤖 AI: {text}")

    async def _generate(tmp_path):
        tts = edge_tts.Communicate(text, voice="en-US-JennyNeural")
        await tts.save(tmp_path)

    tmp      = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tmp_path = tmp.name
    tmp.close()

    asyncio.run(_generate(tmp_path))

    pygame.mixer.music.load(tmp_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.05)

    pygame.mixer.music.unload()
    try:
        os.remove(tmp_path)
    except Exception:
        pass
    time.sleep(0.4)


# ============================================================
# AUTO-SELECT MICROPHONE
# ============================================================
def get_microphone():
    try:
        default = sd.query_devices(kind='input')
        print(f"🎤 Auto-selected microphone: {default['name']}")
        return None
    except Exception as e:
        print(f"⚠️ Mic error: {e}")
        devices = sd.query_devices()
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                return i
        return None


# ============================================================
# RECORD AUDIO
# ============================================================
def record_until_silence(device_index, threshold=0.08, fs=16000):
    print("\n🎤 Listening...\n")

    stream    = sd.InputStream(samplerate=fs, channels=1, device=device_index)
    recording = []
    silence_counter = 0
    has_speech = False

    stream.start()
    try:
        while True:
            audio, _ = stream.read(int(0.5 * fs))
            volume   = np.linalg.norm(audio)
            print(f"   Volume: {volume:.4f}")
            recording.append(audio)

            if volume > threshold:
                has_speech = True
                silence_counter = 0
            elif has_speech:
                silence_counter += 1

            if has_speech and silence_counter > 8:
                break
            if len(recording) > 40:
                break
    finally:
        stream.stop()
        stream.close()

    if not recording or not has_speech:
        return None

    audio_data = np.concatenate(recording, axis=0)
    temp_file  = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    wav.write(temp_file.name, fs, audio_data)
    return temp_file.name


# ============================================================
# TRANSCRIBE
# ============================================================
NOISE_PHRASES = {
    "", "you", "the", "a", "uh", "um", "hmm", "hm", "oh",
    "bye", "hi", "hey", "okay", "ok", "yes", "no", "thank you", "thanks"
}

def transcribe_audio(filepath):
    # Force English transcription to avoid random language detection
    result = model.transcribe(filepath, language="en", task="transcribe")
    text   = result["text"].strip()
    print(f"🗣  User: {text}")

    if len(text.lower().split()) <= 1 and text.lower().strip() in NOISE_PHRASES:
        print("⚠️  Noise filtered:", text)
        try: os.remove(filepath)
        except: pass
        return ""

    try: os.remove(filepath)
    except: pass
    return text


# ============================================================
# GET GPS LOCATION (IP-based fallback)
# ============================================================
def get_gps_location():
    """
    Try to get device location via IP geolocation.
    Returns city string or None.
    """
    try:
        import geocoder
        g = geocoder.ip('me')
        if g.ok and g.city:
            print(f"📍 GPS/IP location detected: {g.city}, {g.country}")
            return g.city, g.latlng
        return None, None
    except Exception as e:
        print(f"⚠️  GPS lookup failed: {e}")
        return None, None


# ============================================================
# DISPATCH AMBULANCE (simulated — replace with real API)
# ============================================================
def dispatch_ambulance(patient_name, location_city, lat_lng, patient_condition):
    """
    Simulates ambulance dispatch.
    In production: integrate with local emergency services API.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    dispatch_record = {
        "dispatched_at":   now,
        "patient_name":    patient_name,
        "condition":       patient_condition,
        "location_city":   location_city,
        "coordinates":     lat_lng,
        "status":          "AMBULANCE DISPATCHED",
        "eta_minutes":     8,
    }

    # Save dispatch log
    log_file = "data/ambulance_dispatch.json"
    os.makedirs("data", exist_ok=True)
    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file) as f:
                content = f.read().strip()
                if content:
                    logs = json.loads(content)
        except Exception:
            pass
    logs.append(dispatch_record)
    with open(log_file, "w") as f:
        json.dump(logs, f, indent=2)

    print(f"\n🚑 AMBULANCE DISPATCHED → {location_city} | ETA: ~8 mins")
    print(f"   Patient  : {patient_name}")
    print(f"   Condition: {patient_condition}")
    print(f"   Coords   : {lat_lng}")
    return dispatch_record


# ============================================================
# EXTRACT LOCATION FROM SPEECH
# ============================================================
# Phrases that mean "use my current location"
NEARBY_PHRASES = [
    "nearest", "near me", "closest", "nearby", "my location",
    "current location", "where i am", "around here", "here",
    "wherever i am", "use my location", "find nearest",
]

def extract_location(user_input):
    text = user_input.lower().strip()

    # ── Detect "nearest hospital" / "my location" type phrases ─
    if any(phrase in text for phrase in NEARBY_PHRASES):
        print("📍 User asked for nearest location — trying GPS...")
        city, _ = get_gps_location()
        if city:
            print(f"✅ GPS location used: {city}")
            return city
        else:
            print("⚠️  GPS failed, will ask user for city")
            return None

    prompt = f"""
Extract the CITY or LOCATION from this spoken message.
User said: "{user_input}"
Return ONLY JSON: {{"location": "value"}} or {{}}
No explanation. No markdown. Only JSON.
Examples: "I am in Berlin" → {{"location": "Berlin"}}, "somewhere near London" → {{"location": "London"}}
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
            value  = parsed.get("location", "").strip()
            bad = {"none", "null", "n/a", "not provided", ""}
            if value.lower() not in bad:
                return value
    except Exception as e:
        print(f"⚠️  Location extraction error: {e}")
    return None


# ============================================================
# EXTRACT NORMAL BOOKING FIELD
# ============================================================
BAD_VALUES = {"none", "null", "n/a", "not provided", "not mentioned", "unknown", ""}

def extract_field(user_input, field_hint):

    # ── Reason: accept any meaningful speech directly ─────────
    # No LLM needed — whatever the user says IS the reason
    if field_hint == "reason":
        text = user_input.strip()
        if len(text.split()) >= 2:
            return text
        return None

    if field_hint == "date":
        prompt = f"""
Extract the appointment DATE from: "{user_input}"
Pick the LAST date if multiple. Return ONLY JSON: {{"date": "value"}} or {{}}
No explanation. No markdown.
Examples: "tomorrow"→{{"date":"tomorrow"}}, "24th March"→{{"date":"24th March"}}
"""
    elif field_hint == "time":
        prompt = f"""
Extract the appointment TIME from: "{user_input}"
Convert spoken time to standard format. Return ONLY JSON: {{"time": "value"}} or {{}}
No explanation. No markdown.
Examples: "10 in the morning"→{{"time":"10:00 AM"}}, "morning"→{{"time":"morning"}}
"""
    elif field_hint == "location":
        return extract_location(user_input)
    else:
        prompt = f"""
Extract the medical PROBLEM from: "{user_input}"
Return ONLY JSON: {{"problem": "value"}} or {{}}
No explanation. No markdown.
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
            if value.lower() not in BAD_VALUES:
                return value
    except Exception as e:
        print(f"⚠️  Extraction error [{field_hint}]: {e}")
    return None


# ============================================================
# NORMAL BOOKING QUESTIONS
# ============================================================
QUESTIONS = {
    "reason":   "Your record shows you have {condition}. Is that the reason for today's visit, or is there something else? Please describe.",
    "date":     "What date would you like the appointment? For example, tomorrow or the 25th of March.",
    "time":     "What time would you prefer? For example, 10 in the morning or 2 in the afternoon.",
    "location": "Which city or area would you prefer for the appointment?",
}

RETRY_QUESTIONS = {
    "reason":   "Could you describe the reason for your visit today?",
    "date":     "Could you repeat the date? For example, tomorrow or March 25th.",
    "time":     "What time works for you? Morning, afternoon, or a specific time?",
    "location": "I could not detect your location automatically. Please say your city name clearly, for example Berlin or London.",
}

NORMAL_FIELDS = ["reason", "date", "time", "location"]


# ============================================================
# EMERGENCY FLOW
# ============================================================
def handle_emergency_flow(device_index, details, patient_id, patient):
    """
    Dedicated emergency flow:
    1. Try GPS auto-detect
    2. If GPS fails → ask user for location by voice
    3. Dispatch ambulance
    4. Book emergency appointment
    """
    patient_name      = details["name"]
    patient_condition = details["problem"]

    speak("This is an emergency! Stay calm. I am getting help for you right now.")
    time.sleep(0.3)

    # ── Step 1: Try GPS / IP location ────────────────────────
    speak("Let me try to find your location automatically.")
    city, lat_lng = get_gps_location()

    if city:
        speak(f"I found your location: {city}. Dispatching an ambulance now!")
        details["location"] = city
    else:
        # ── Step 2: Ask for location by voice ─────────────────
        speak("I could not detect your location automatically. Please tell me your city or address.")

        location = None
        retry    = 0

        while not location and retry < 4:
            audio_file = record_until_silence(device_index)

            if not audio_file:
                retry += 1
                speak("I didn't hear you. Please say your city name.")
                continue

            user_input = transcribe_audio(audio_file)

            if not user_input or len(user_input.strip()) < 2:
                retry += 1
                speak("I couldn't hear clearly. Please say your city or area.")
                continue

            location = extract_location(user_input)

            if location:
                speak(f"Got it. Your location is {location}. Dispatching ambulance now!")
                details["location"] = location
            else:
                retry += 1
                speak("I couldn't understand the location. Please say just the city name.")

        if not location:
            speak("I was unable to get your location. Please call emergency services immediately!")
            return None

    # ── Step 3: Dispatch ambulance ────────────────────────────
    lat_lng = lat_lng or [0, 0]
    dispatch = dispatch_ambulance(
        patient_name      = patient_name,
        location_city     = details["location"],
        lat_lng           = lat_lng,
        patient_condition = patient_condition
    )

    speak(f"Ambulance has been dispatched to {details['location']}. Estimated arrival is {dispatch['eta_minutes']} minutes.")
    speak("Please stay where you are and keep this line open.")

    # ── Step 4: Book emergency appointment ───────────────────
    now = datetime.now()
    details["date"] = now.strftime("%d %B %Y")
    details["time"] = now.strftime("%H:%M")

    location_data = get_location_details(details["location"])
    if not location_data:
        # Fallback location data if service fails
        location_data = {
            "full_address": details["location"],
            "city":         details["location"],
            "country":      "Unknown"
        }

    appointment = book_appointment(
        patient_id,
        patient,
        location_data,
        patient.get("insurance", "none"),
        details
    )

    speak(f"Emergency appointment confirmed with {appointment['doctor']}. Help is on the way!")
    return appointment


# ============================================================
# MAIN FUNCTION
# ============================================================
def run_ai_call(patient_id, patient) -> dict | None:

    device_index = get_microphone()

    patient_name      = patient.get("name", "")
    patient_condition = patient.get("condition", "")
    allergies         = patient.get("allergies", [])
    allergy_str       = ', '.join(allergies) if isinstance(allergies, list) else str(allergies)

    # Pre-fill from patient record
    details = {
        "name":      patient_name,
        "phone":     patient.get("phone", ""),
        "problem":   None,   # always asked fresh — user may have a different reason today
        "notes":     f"Allergies: {allergy_str}. "
                     f"Doctor notes: {patient.get('last_visit', {}).get('doctor_notes', '')}",
        "emergency": False,
        "reason":    None,   # collected by voice
        "date":      None,
        "time":      None,
        "location":  None,
    }

    # ── Check if patient condition is already an emergency ───
    if detect_emergency(patient_condition):
        details["emergency"] = True
        speak(f"Hello {patient_name}. Your condition {patient_condition} is flagged as an emergency.")
        return handle_emergency_flow(device_index, details, patient_id, patient)

    # ── Normal greeting ───────────────────────────────────────
    speak(f"Hello {patient_name}! I can see you are registered for {patient_condition}.")
    speak("I have a few quick questions to book your appointment.")

    # Inject patient condition into reason question
    QUESTIONS["reason"] = QUESTIONS["reason"].replace("{condition}", patient_condition)

    current_field = NORMAL_FIELDS[0]   # "reason"
    speak(QUESTIONS[current_field])
    retry_count = 0

    # ── Normal booking loop ───────────────────────────────────
    while True:

        audio_file = record_until_silence(device_index)

        if not audio_file:
            retry_count += 1
            if retry_count >= 3:
                speak("I'm having trouble hearing you. Please try again later.")
                break
            speak(f"I didn't hear anything. {RETRY_QUESTIONS.get(current_field, '')}")
            continue

        user_input = transcribe_audio(audio_file)

        if not user_input or len(user_input.strip()) < 3:
            retry_count += 1
            if retry_count >= 3:
                speak("I'm having trouble hearing you. Please try again later.")
                break
            speak(RETRY_QUESTIONS.get(current_field, QUESTIONS[current_field]))
            continue

        if "stop" in user_input.lower():
            speak("Stopping now. Goodbye, take care!")
            break

        # ── Real-time emergency detection ─────────────────────
        # If user says something like "severe chest pain" MID conversation
        if detect_emergency(user_input):
            details["emergency"] = True
            details["problem"]   = user_input.strip()
            speak("This sounds like an emergency! I am switching to emergency mode.")
            return handle_emergency_flow(device_index, details, patient_id, patient)

        # ── Save answer for current field ─────────────────────
        # Check for emergency in every answer
        if detect_emergency(user_input):
            details["emergency"] = True
            details["problem"]   = user_input.strip()
            speak("This sounds like an emergency! Switching to emergency mode now.")
            return handle_emergency_flow(device_index, details, patient_id, patient)

        value = extract_field(user_input, current_field)

        if not value and current_field == "reason":
            # Accept any meaningful speech as the reason
            if len(user_input.strip().split()) >= 2:
                value = user_input.strip()

        if value:
            details[current_field] = value
            if current_field == "reason":
                details["problem"] = value  # save reason as problem too
            print(f"✅  Saved {current_field}: {value}")
            retry_count = 0
        else:
            retry_count += 1
            print(f"⚠️  Could not extract '{current_field}' from: '{user_input}'")
            if retry_count >= 3:
                details[current_field] = "not provided"
                retry_count = 0
            else:
                speak(RETRY_QUESTIONS.get(current_field, QUESTIONS[current_field]))
                continue

        # ── Next missing field ────────────────────────────────
        missing = [f for f in NORMAL_FIELDS if not details.get(f)]

        if not missing:
            speak(f"Thank you {patient_name}! Booking your appointment now.")
            break

        current_field = missing[0]
        speak(QUESTIONS[current_field])

    # ============================================================
    # NORMAL BOOKING
    # ============================================================
    print("\n📋 Final Details:")
    for k, v in details.items():
        print(f"   {k:12s}: {v}")

    invalid    = {None, "", "none", "not provided", "n/a"}
    core_ready = all(
        str(details.get(f, "")).lower().strip() not in invalid
        for f in NORMAL_FIELDS
    )

    if core_ready:
        location_data = get_location_details(details["location"])
        if not location_data:
            speak("Sorry, I could not find that location. Please try again.")
            return None

        appointment = book_appointment(
            patient_id,
            patient,
            location_data,
            patient.get("insurance", "none"),
            details
        )

        speak(
            f"Your appointment is booked for {details.get('date')} "
            f"at {details.get('time')} with {appointment['doctor']}!"
        )
        return appointment

    else:
        speak("I was unable to collect all required details. Please try again.")
        return None