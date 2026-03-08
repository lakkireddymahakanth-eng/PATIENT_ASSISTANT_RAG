import sys
import os

# allow project root imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
from src.main import ask_question
from src.services.report_service import extract_pdf_text
from src.services.report_analysis import analyze_medical_report
from src.services.patient_service import load_patient
from src.core.rag_engine import RAGEngine


st.set_page_config(
    page_title="Patient RAG Assistant",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 Patient Medical Assistant")

rag = RAGEngine()


# ---------------------------
# Sidebar
# ---------------------------
with st.sidebar:

    st.header("Patient Settings")

    patient_id = st.text_input(
        "Enter your Patient ID",
        placeholder="Example: P012"
    )

    # ---------------------------
    # Patient Dashboard
    # ---------------------------
    patient_data = None

    if patient_id:

        patient_data = load_patient(patient_id)

        if patient_data:

            st.markdown("### Patient Overview")

            st.write(f"Name: {patient_data['name']}")
            st.write(f"Age: {patient_data['age']}")
            st.write(f"Condition: {patient_data['condition']}")

            allergies = patient_data.get("allergies", [])

            if allergies:
                st.write(f"Allergies: {', '.join(allergies)}")

            visit = patient_data.get("last_visit", {})

            st.markdown("### Doctor Notes")
            st.write(visit.get("doctor_notes", "No notes"))

            st.markdown("### Diet Plan")
            st.write(visit.get("diet_plan", "No diet plan"))

        else:
            st.warning("Patient ID not found.")

    st.markdown("---")

    # ---------------------------
    # Patient Report Timeline
    # ---------------------------
    if patient_id:

        report_folder = os.path.join("uploads", patient_id)

        st.markdown("### Patient Reports")

        if os.path.exists(report_folder):

            files = os.listdir(report_folder)

            if files:

                for file in files:

                    file_path = os.path.join(report_folder, file)

                    col1, col2, col3 = st.columns([5, 1, 1])

                    col1.write(file)

                    with open(file_path, "rb") as f:
                        file_bytes = f.read()

                    col2.download_button(
                        label="Download",
                        data=file_bytes,
                        file_name=file,
                        mime="application/octet-stream"
                    )

                    if file.endswith(".txt"):

                        with col3.expander("View"):

                            with open(file_path, "r") as f:
                                st.write(f.read())

            else:
                st.write("No reports uploaded yet.")

        else:
            st.write("No reports uploaded yet.")

    st.markdown("---")

    # ---------------------------
    # Upload Medical Reports
    # ---------------------------
    st.subheader("Upload Medical Report")

    uploaded_file = st.file_uploader(
        "Upload report (PDF or TXT)",
        type=["pdf", "txt"]
    )

    if uploaded_file is not None and patient_id:

        patient_folder = os.path.join("uploads", patient_id)

        os.makedirs(patient_folder, exist_ok=True)

        file_path = os.path.join(patient_folder, uploaded_file.name)

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success("Report uploaded successfully")

        # Extract report text
        if uploaded_file.name.endswith(".pdf"):

            text = extract_pdf_text(file_path)

        else:

            with open(file_path, "r") as f:
                text = f.read()

        # ---------------------------
        # AI REPORT ANALYSIS
        # ---------------------------
        with st.spinner("Analyzing report..."):

            summary = analyze_medical_report(text)

        st.subheader("📋 Report Summary")

        st.markdown(summary)

        # ---------------------------
        # Store report in RAG DB
        # ---------------------------
        rag.index_patient_report(patient_id, text)

        st.success("Report added to patient knowledge base")

    st.markdown("---")

    if st.button("Clear Conversation"):

        st.session_state.messages = []

        st.rerun()

    st.caption("AI assistant for patient pre/post treatment guidance")


# ---------------------------
# Chat Memory
# ---------------------------
if "messages" not in st.session_state:

    st.session_state.messages = []


# ---------------------------
# Display Chat Messages
# ---------------------------
for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):

        st.markdown(msg["content"])


# ---------------------------
# Chat Input
# ---------------------------
if prompt := st.chat_input("Ask your health question..."):

    if not patient_id:

        st.warning("Please enter your Patient ID first.")

        st.stop()

    # Show user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate AI response
    with st.chat_message("assistant"):

        chat_history = [
            (m["content"], "")
            for m in st.session_state.messages
            if m["role"] == "user"
        ]

        response_placeholder = st.empty()

        full_response = ""

        for chunk in ask_question(patient_id, prompt, chat_history):

            full_response += chunk

            response_placeholder.markdown(full_response + "▌")

        response_placeholder.markdown(full_response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response
    })