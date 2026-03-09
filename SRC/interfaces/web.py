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


# ----------------------------------------------------
# Page Config
# ----------------------------------------------------
st.set_page_config(
    page_title="AI Patient Assistant",
    page_icon="🏥",
    layout="wide"
)

st.markdown(
"""
# 🏥 AI Patient Medical Assistant
### Intelligent support for patient recovery and health monitoring
"""
)

rag = RAGEngine()


# ----------------------------------------------------
# Layout
# ----------------------------------------------------
left, right = st.columns([1, 2])


# ====================================================
# LEFT PANEL — PATIENT DASHBOARD
# ====================================================
with left:

    st.header("🧑 Patient Dashboard")

    patient_id = st.text_input(
        "Enter Patient ID",
        placeholder="Example: P012"
    )

    patient_data = None

    if patient_id:

        patient_data = load_patient(patient_id)

        if patient_data:

            st.success("Patient Loaded")

            st.markdown("### Patient Overview")

            st.info(f"""
**Name:** {patient_data['name']}

**Age:** {patient_data['age']}

**Condition:** {patient_data['condition']}
""")

            allergies = patient_data.get("allergies", [])

            if allergies:
                st.warning(f"⚠️ Allergies: {', '.join(allergies)}")

            visit = patient_data.get("last_visit", {})

            st.markdown("### Doctor Notes")
            st.write(visit.get("doctor_notes", "No notes available"))

            st.markdown("### Diet Plan")
            st.write(visit.get("diet_plan", "No diet plan available"))

        else:
            st.error("Patient ID not found")


    st.markdown("---")


    # ----------------------------------------------------
    # Patient Reports
    # ----------------------------------------------------
    if patient_id:

        st.markdown("### 📄 Medical Reports")

        report_folder = os.path.join("uploads", patient_id)

        if os.path.exists(report_folder):

            files = os.listdir(report_folder)

            if files:

                for file in files:

                    file_path = os.path.join(report_folder, file)

                    with st.container(border=True):

                        st.write(f"📄 {file}")

                        with open(file_path, "rb") as f:
                            file_bytes = f.read()

                        st.download_button(
                            "Download",
                            file_bytes,
                            file
                        )

            else:
                st.write("No reports uploaded yet")

        else:
            st.write("No reports uploaded yet")


    st.markdown("---")


    # ----------------------------------------------------
    # Upload Reports
    # ----------------------------------------------------
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

        # Extract text
        if uploaded_file.name.endswith(".pdf"):
            text = extract_pdf_text(file_path)
        else:
            with open(file_path, "r") as f:
                text = f.read()

        # Analyze report
        with st.spinner("🔬 AI analyzing report..."):
            summary = analyze_medical_report(text)

        st.markdown("### 📋 Report Summary")
        st.markdown(summary)

        rag.index_patient_report(patient_id, text)

        st.success("Report added to patient knowledge base")


# ====================================================
# RIGHT PANEL — CHAT ASSISTANT
# ====================================================
with right:

    st.header("💬 Medical Assistant Chat")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:

        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


    # ----------------------------------------------------
    # Chat Input
    # ----------------------------------------------------
    if prompt := st.chat_input("Ask your health question..."):

        if not patient_id:
            st.warning("Please enter Patient ID first")
            st.stop()

        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        # AI response
        with st.chat_message("assistant"):

            with st.spinner("🤖 AI analyzing medical knowledge..."):

                response = ask_question(patient_id, prompt)

                st.markdown(response)

        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })


    st.markdown("---")
    st.caption("AI Patient Assistant • Powered by Local LLM + RAG")