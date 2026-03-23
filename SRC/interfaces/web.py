import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st

from src.main import ask_question
from src.services.report_service import extract_pdf_text
from src.services.report_analysis import analyze_medical_report
from src.services.patient_service import load_patient
from src.services.image_service import extract_image_text
from src.services.voice_service import speech_to_text, text_to_speech
from src.core.rag_engine import RAGEngine

# ------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------
st.set_page_config(
    page_title="Patient Assistance",
    page_icon="🏥",
    layout="wide"
)

rag = RAGEngine()

# ------------------------------------------------
# SESSION STATE
# ------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "show_upload" not in st.session_state:
    st.session_state.show_upload = False

if "show_booking" not in st.session_state:
    st.session_state.show_booking = False

# Chat booking state
if "chat_started" not in st.session_state:
    st.session_state.chat_started = False

if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False

if "chat_details" not in st.session_state:
    st.session_state.chat_details = {}

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "booked_appointment" not in st.session_state:
    st.session_state.booked_appointment = None

if "emergency_dispatch" not in st.session_state:
    st.session_state.emergency_dispatch = {}

# ------------------------------------------------
# CSS
# ------------------------------------------------
st.markdown("""
<style>
.chat-bar {
    position: fixed;
    bottom: 10px;
    left: 260px;
    right: 20px;
    background: white;
    padding: 12px;
    border-radius: 12px;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.15);
    z-index: 999;
}
.block-container {
    padding-bottom: 120px;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# SIDEBAR
# ------------------------------------------------
with st.sidebar:

    st.header("Patient Dashboard")

    patient_id = st.text_input(
        "Enter Patient ID",
        placeholder="Example: P012"
    )

    patient_data = None

    if patient_id:
        patient_data = load_patient(patient_id)

        if patient_data:
            st.success("Patient Loaded")
            st.write("Name:", patient_data["name"])
            st.write("Age:", patient_data["age"])
            st.write("Condition:", patient_data["condition"])

            allergies = patient_data.get("allergies", [])
            if allergies:
                allergy_str = ', '.join(allergies) if isinstance(allergies, list) else str(allergies)
                st.warning(f"Allergies: {allergy_str}")

            visit = patient_data.get("last_visit", {})

            st.markdown("### Doctor Notes")
            st.write(visit.get("doctor_notes", "No notes"))

            st.markdown("### Diet Plan")
            st.write(visit.get("diet_plan", "No diet plan"))

        else:
            st.error("Patient ID not found")

# ------------------------------------------------
# TITLE + BOOK BUTTON
# ------------------------------------------------
col1, col2 = st.columns([8, 2])

with col1:
    st.title("🏥 Patient Assistance")

with col2:
    if st.button("📅 Book Appointment"):
        st.session_state.show_booking = not st.session_state.show_booking

# ------------------------------------------------
# BOOKING UI
# ------------------------------------------------
if st.session_state.show_booking:

    st.markdown("## Appointment Options")

    if not patient_id or not patient_data:
        st.warning("⚠️ Please enter a valid Patient ID first.")
        st.stop()

    mode = st.radio("Choose Mode", ["💬 Chat Booking", "🤖 AI Voice Booking"])

    # =========================================================
    # 💬 CHAT BOOKING
    # =========================================================
    if mode == "💬 Chat Booking":

        st.markdown("### Start booking via chat")
        st.info("💡 Just describe your problem and the AI will guide you step-by-step.")

        # ── Start button ──────────────────────────────────────
        if not st.session_state.chat_started:
            if st.button("Start Chat Booking"):

                from src.services.conversation_engine import get_greeting

                # Pre-fill from patient record
                allergies = patient_data.get("allergies", [])
                allergy_str = ', '.join(allergies) if isinstance(allergies, list) else str(allergies)

                st.session_state.chat_details = {
                    "name":      patient_data.get("name", ""),
                    "phone":     patient_data.get("phone", ""),
                    "problem":   None,   # collected fresh via reason question
                    "notes":     f"Allergies: {allergy_str}. "
                                 f"Doctor notes: {patient_data.get('last_visit', {}).get('doctor_notes', '')}",
                    "emergency": False,
                    "reason":    None,
                    "date":      None,
                    "time":      None,
                    "location":  None,
                }

                st.session_state.chat_history  = []
                st.session_state.chat_started  = True
                st.session_state.chat_complete = False
                st.session_state.booked_appointment = None

                # Add greeting to chat
                greeting = get_greeting(patient_data)
                st.session_state.chat_history.append({
                    "role": "assistant", "content": greeting
                })

                st.rerun()

        # ── Active chat ───────────────────────────────────────
        if st.session_state.chat_started:

            # Show booked appointment if done
            if st.session_state.booked_appointment:
                appt = st.session_state.booked_appointment
                st.success(f"✅ Appointment booked! ID: **{appt['appointment_id']}**")
                st.markdown(f"""
| Field | Value |
|---|---|
| 👤 Name | {appt.get('name', '')} |
| 🩺 Problem | {appt.get('problem', '')} |
| 👨‍⚕️ Doctor | {appt.get('doctor', '')} |
| 🏥 Specialization | {appt.get('specialization', '')} |
| 📅 Date & Time | {appt.get('datetime', '')} |
| 📍 Location | {appt.get('location', {}).get('city', '')} |
""")
                if st.button("📅 Book Another Appointment"):
                    st.session_state.chat_started  = False
                    st.session_state.chat_complete = False
                    st.session_state.chat_details  = {}
                    st.session_state.chat_history  = []
                    st.session_state.booked_appointment = None
                    st.rerun()

            else:
                # Display chat messages
                for msg in st.session_state.chat_history:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

                # Chat input — only if not complete
                if not st.session_state.chat_complete:
                    user_input = st.chat_input("Type your answer here...")

                    if user_input:
                        from src.services.conversation_engine import process_chat_message
                        from src.services.conversation_history_service import save_conversation
                        from src.services.location_service import get_location_details
                        from src.services.appointment_service import book_appointment, dispatch_ambulance, detect_emergency
                        from src.services.ai_voice_call import extract_location

                        st.session_state.chat_history.append({
                            "role": "user", "content": user_input
                        })

                        # ── Emergency location correction ─────────────
                        dispatch_info = st.session_state.get("emergency_dispatch", {})
                        is_emergency  = st.session_state.chat_details.get("emergency", False)

                        if is_emergency and dispatch_info:
                            # User is correcting or confirming location
                            corrected_city = extract_location(user_input)

                            if corrected_city:
                                old_city = dispatch_info.get("city", "")
                                eta      = 8

                                if corrected_city.lower() != (old_city or "").lower():
                                    # Re-dispatch to new location
                                    new_dispatch = dispatch_ambulance(
                                        patient_name      = patient_data.get("name", ""),
                                        location_city     = corrected_city,
                                        lat_lng           = [0, 0],
                                        patient_condition = dispatch_info.get("problem", "")
                                    )
                                    eta = new_dispatch.get("eta_minutes", 8)
                                    ai_response = (
                                        f"✅ Got it! I have redirected the ambulance to **{corrected_city}**. "
                                        f"Estimated arrival: ~{eta} minutes. Please stay where you are."
                                    )
                                    st.session_state.emergency_dispatch["city"] = corrected_city
                                else:
                                    # User confirmed the GPS location
                                    ai_response = (
                                        f"✅ Location confirmed: **{corrected_city}**. "
                                        f"The ambulance is on its way. ETA ~{eta} minutes. Stay calm and keep this open."
                                    )

                                st.session_state.chat_details["location"] = corrected_city

                            elif any(w in user_input.lower() for w in ["yes", "correct", "right", "confirmed", "ok", "that's right"]):
                                city = dispatch_info.get("city", "your location")
                                eta  = dispatch_info.get("eta", 8)
                                ai_response = (
                                    f"✅ Location confirmed: **{city}**. "
                                    f"Ambulance is on its way. ETA ~{eta} minutes. Stay calm."
                                )
                            else:
                                ai_response = (
                                    f"🚨 Please type your **city name** so I can direct the ambulance correctly. "
                                    f"For example: Berlin, London, Mumbai."
                                )

                            st.session_state.chat_history.append({
                                "role": "assistant", "content": ai_response
                            })

                            # Book emergency appointment in background
                            loc = st.session_state.chat_details.get("location")
                            if loc and not st.session_state.chat_complete:
                                from datetime import datetime as _dt
                                now = _dt.now()
                                st.session_state.chat_details["date"] = now.strftime("%d %B %Y")
                                st.session_state.chat_details["time"] = now.strftime("%H:%M")
                                location_data = get_location_details(loc) or {
                                    "full_address": loc, "city": loc, "country": ""
                                }
                                try:
                                    appointment = book_appointment(
                                        patient_id, patient_data, location_data,
                                        patient_data.get("insurance", "none"),
                                        st.session_state.chat_details
                                    )
                                    st.session_state.booked_appointment = appointment
                                    st.session_state.chat_complete = True
                                    save_conversation(patient_id, st.session_state.chat_history)
                                except Exception as e:
                                    print(f"Emergency booking error: {e}")

                            st.rerun()

                        else:
                            # ── Normal chat flow ──────────────────────
                            ai_response, updated_details, is_complete = process_chat_message(
                                user_input,
                                st.session_state.chat_details,
                                patient_data,
                                st.session_state.chat_history
                            )
                            st.session_state.chat_details = updated_details
                            st.session_state.chat_history.append({
                                "role": "assistant", "content": ai_response
                            })

                            if is_complete:
                                st.session_state.chat_complete = True
                                location_data = get_location_details(
                                    st.session_state.chat_details.get("location", "")
                                )
                                if location_data:
                                    try:
                                        appointment = book_appointment(
                                            patient_id, patient_data, location_data,
                                            patient_data.get("insurance", "none"),
                                            st.session_state.chat_details
                                        )
                                        st.session_state.booked_appointment = appointment
                                        save_conversation(patient_id, st.session_state.chat_history)
                                    except Exception as e:
                                        st.error(f"❌ Booking failed: {e}")
                                        st.session_state.chat_complete = False
                                else:
                                    st.session_state.chat_details["location"] = None
                                    st.session_state.chat_complete = False
                                    st.session_state.chat_history.append({
                                        "role": "assistant",
                                        "content": "Sorry, I couldn't find that location. Could you please type the city name again?"
                                    })

                            st.rerun()

    # =========================================================
    # 🤖 AI VOICE BOOKING
    # =========================================================
    elif mode == "🤖 AI Voice Booking":

        st.markdown("### AI Voice Assistant")
        st.info("🎤 AI will talk to you and collect all details.")

        if st.button("Start AI Voice Call"):

            from src.services.ai_voice_call import run_ai_call

            with st.spinner("🎤 AI is interacting with you..."):
                appointment = run_ai_call(patient_id, patient_data)

            if appointment:
                st.success("✅ Appointment booked via AI!")
                st.markdown(f"""
| Field | Value |
|---|---|
| 👤 Name | {appointment.get('name', '')} |
| 📞 Phone | {appointment.get('phone', '')} |
| 🩺 Problem | {appointment.get('problem', '')} |
| 👨‍⚕️ Doctor | {appointment.get('doctor', '')} |
| 🏥 Specialization | {appointment.get('specialization', '')} |
| 📅 Date & Time | {appointment.get('datetime', '')} |
| 📍 Location | {appointment.get('location', {}).get('address', '')} |
""")
            else:
                st.error("❌ AI booking failed. Please try again.")

# ------------------------------------------------
# DISPLAY CHAT HISTORY
# ------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ------------------------------------------------
# CHAT BAR
# ------------------------------------------------
st.markdown('<div class="chat-bar">', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 10, 1])

with col1:
    if st.button("➕"):
        st.session_state.show_upload = True

with col2:
    prompt = st.chat_input("Ask your health question...")

with col3:
    mic_clicked = st.button("🎤")

st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------
# FILE UPLOAD
# ------------------------------------------------
if st.session_state.show_upload:

    uploaded_file = st.file_uploader(
        "Upload Report",
        type=["pdf", "txt", "png", "jpg", "jpeg"]
    )

    if uploaded_file and patient_id:

        patient_folder = os.path.join("uploads", patient_id)
        os.makedirs(patient_folder, exist_ok=True)

        file_path = os.path.join(patient_folder, uploaded_file.name)

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success("Report uploaded")

        if uploaded_file.name.endswith(".pdf"):
            text = extract_pdf_text(file_path)

        elif uploaded_file.name.endswith((".png", ".jpg", ".jpeg")):
            text = extract_image_text(file_path)

        else:
            text = uploaded_file.read().decode()

        with st.spinner("Analyzing report..."):
            summary = analyze_medical_report(text)

        st.markdown("### Report Summary")
        st.markdown(summary)

        rag.index_patient_report(patient_id, text)

        st.session_state.show_upload = False

# ------------------------------------------------
# TEXT QUESTION
# ------------------------------------------------
if prompt:

    if not patient_id:
        st.warning("Please enter Patient ID first")
        st.stop()

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    # ── Emergency detection in general chat ──────────────────
    from src.services.appointment_service import detect_emergency, dispatch_ambulance
    from src.services.ai_voice_call import get_gps_location
    from src.services.location_service import get_location_details

    if detect_emergency(prompt) and patient_data:

        patient_name = patient_data.get("name", "Patient")
        allergies    = patient_data.get("allergies", [])
        allergy_str  = ", ".join(allergies) if isinstance(allergies, list) else str(allergies)

        # ── Try GPS/IP auto-detect ────────────────────────────
        gps_city, lat_lng = get_gps_location()

        if gps_city:
            # GPS found — dispatch immediately, ask to confirm
            dispatch = dispatch_ambulance(
                patient_name      = patient_name,
                location_city     = gps_city,
                lat_lng           = lat_lng or [0, 0],
                patient_condition = prompt
            )
            eta = dispatch.get("eta_minutes", 8)

            emergency_msg = (
                f"🚨 **Emergency detected!**\n\n"
                f"🛰️ GPS shows you are near **{gps_city}**.\n\n"
                f"🚑 **An ambulance has been dispatched to {gps_city}. "
                f"Estimated arrival: ~{eta} minutes.**\n\n"
                f"⚠️ If this location is wrong, please type your correct city below "
                f"and I will redirect the ambulance immediately.\n\n"
                f"📞 **Also call 112 / 911 if the situation is critical.**"
            )

            # Save dispatch to session so user can correct it
            st.session_state.emergency_dispatch = {
                "dispatched": True,
                "city":       gps_city,
                "eta":        eta,
                "problem":    prompt,
            }

        else:
            # GPS failed — ask for location
            emergency_msg = (
                f"🚨 **Emergency detected!**\n\n"
                f"I could not detect your location automatically.\n\n"
                f"Please **type your city or address below** and I will "
                f"dispatch an ambulance immediately.\n\n"
                f"📞 **Also call 112 / 911 right now if the situation is critical.**"
            )
            st.session_state.emergency_dispatch = {
                "dispatched": False,
                "city":       None,
                "problem":    prompt,
            }

        with st.chat_message("assistant"):
            st.markdown(emergency_msg)
            try:
                tts_text = (
                    f"Emergency detected. An ambulance has been dispatched to {gps_city}. ETA {eta} minutes. Please confirm your location."
                    if gps_city else
                    "Emergency detected. I could not find your location. Please type your city immediately."
                )
                audio_file = text_to_speech(tts_text)
                st.audio(audio_file)
            except Exception:
                pass

        st.session_state.messages.append({"role": "assistant", "content": emergency_msg})

        # Set up emergency chat to handle location correction
        st.session_state.show_booking  = True
        st.session_state.chat_started  = True
        st.session_state.chat_complete = False
        st.session_state.chat_details  = {
            "name":      patient_name,
            "phone":     patient_data.get("phone", ""),
            "problem":   prompt,
            "notes":     f"Allergies: {allergy_str}",
            "emergency": True,
            "reason":    prompt,
            "date":      None,
            "time":      None,
            "location":  gps_city,   # pre-filled if GPS worked
        }
        st.session_state.chat_history = [
            {"role": "user",      "content": prompt},
            {"role": "assistant", "content": emergency_msg},
        ]
        st.rerun()

    else:
        with st.chat_message("assistant"):

            with st.spinner("AI thinking..."):

                response = ""

                for chunk in ask_question(patient_id, prompt):
                    response += chunk

                st.markdown(response)

                audio_file = text_to_speech(response)
                st.audio(audio_file)

        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })

# ------------------------------------------------
# VOICE QUESTION
# ------------------------------------------------
if mic_clicked:

    if not patient_id:
        st.warning("Please enter Patient ID first")
        st.stop()

    spoken_text = speech_to_text()

    st.info(f"You said: {spoken_text}")

    st.session_state.messages.append({
        "role": "user",
        "content": spoken_text
    })

    with st.chat_message("assistant"):

        with st.spinner("AI thinking..."):

            response = ""

            for chunk in ask_question(patient_id, spoken_text):
                response += chunk

            st.markdown(response)

            audio_file = text_to_speech(response)
            st.audio(audio_file)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })

# ------------------------------------------------
# FOOTER
# ------------------------------------------------
st.markdown(
    """
<div style='position:fixed;bottom:10px;right:20px;color:black;font-size:14px'>
Patient Assistance • AI Healthcare System
</div>
""",
    unsafe_allow_html=True
)