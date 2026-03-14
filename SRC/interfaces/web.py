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
# CSS (CHATGPT STYLE INPUT BAR)
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
                st.warning(f"Allergies: {', '.join(allergies)}")

            visit = patient_data.get("last_visit", {})

            st.markdown("### Doctor Notes")
            st.write(visit.get("doctor_notes", "No notes"))

            st.markdown("### Diet Plan")
            st.write(visit.get("diet_plan", "No diet plan"))

        else:
            st.error("Patient ID not found")


# ------------------------------------------------
# TITLE
# ------------------------------------------------

st.title("🏥 Patient Assistance")


# ------------------------------------------------
# CHAT MEMORY
# ------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "show_upload" not in st.session_state:
    st.session_state.show_upload = False


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

col1, col2, col3 = st.columns([1,10,1])

# ➕ attachment
with col1:
    if st.button("➕"):
        st.session_state.show_upload = True

# text input
with col2:
    prompt = st.chat_input("Ask your health question...")

# mic
with col3:
    mic_clicked = st.button("🎤")

st.markdown('</div>', unsafe_allow_html=True)


# ------------------------------------------------
# FILE UPLOAD
# ------------------------------------------------

if st.session_state.show_upload:

    uploaded_file = st.file_uploader(
        "Upload Report",
        type=["pdf","txt","png","jpg","jpeg"]
    )

    if uploaded_file and patient_id:

        patient_folder = os.path.join("uploads", patient_id)
        os.makedirs(patient_folder, exist_ok=True)

        file_path = os.path.join(patient_folder, uploaded_file.name)

        with open(file_path,"wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success("Report uploaded")

        if uploaded_file.name.endswith(".pdf"):

            text = extract_pdf_text(file_path)

        elif uploaded_file.name.endswith((".png",".jpg",".jpeg")):

            text = extract_image_text(file_path)

        else:

            text = uploaded_file.read().decode()

        with st.spinner("Analyzing report..."):

            summary = analyze_medical_report(text)

        st.markdown("### Report Summary")
        st.markdown(summary)

        rag.index_patient_report(patient_id,text)

        st.session_state.show_upload = False


# ------------------------------------------------
# TEXT QUESTION
# ------------------------------------------------

if prompt:

    if not patient_id:
        st.warning("Please enter Patient ID first")
        st.stop()

    st.session_state.messages.append({
        "role":"user",
        "content":prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):

        with st.spinner("AI thinking..."):

            response = ""

            for chunk in ask_question(patient_id,prompt):
                response += chunk

            st.markdown(response)

            audio_file = text_to_speech(response)
            st.audio(audio_file)

    st.session_state.messages.append({
        "role":"assistant",
        "content":response
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
        "role":"user",
        "content":spoken_text
    })

    with st.chat_message("assistant"):

        with st.spinner("AI thinking..."):

            response = ""

            for chunk in ask_question(patient_id,spoken_text):
                response += chunk

            st.markdown(response)

            audio_file = text_to_speech(response)
            st.audio(audio_file)

    st.session_state.messages.append({
        "role":"assistant",
        "content":response
    })


# ------------------------------------------------
# FOOTER
# ------------------------------------------------

st.markdown(
"""
<div style='position:fixed;bottom:10px;right:20px;color:black;font-size:14px'>
Patient Assistance • Local AI + RAG
</div>
""",
unsafe_allow_html=True
)