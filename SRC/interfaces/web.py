import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
from src.main import ask_question
from src.services.report_service import extract_pdf_text
from src.services.report_analysis import analyze_medical_report
from src.services.patient_service import load_patient
from src.core.rag_engine import RAGEngine
from src.services.image_service import extract_image_text


# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Patient Assistance",
    page_icon="🏥",
    layout="wide"
)

rag = RAGEngine()


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

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
            st.write(visit.get("doctor_notes","No notes"))

            st.markdown("### Diet Plan")
            st.write(visit.get("diet_plan","No diet plan"))

        else:
            st.error("Patient ID not found")


# --------------------------------------------------
# TITLE
# --------------------------------------------------

st.title("🏥 Patient Assistance")


# --------------------------------------------------
# CHAT HISTORY
# --------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# --------------------------------------------------
# DOCUMENT UPLOAD (NOW SUPPORTS IMAGES)
# --------------------------------------------------

st.markdown("---")

uploaded_file = st.file_uploader(
    "Upload Report",
    type=["pdf","txt","png","jpg","jpeg"]
)

if uploaded_file is not None and patient_id:

    patient_folder = os.path.join("uploads", patient_id)
    os.makedirs(patient_folder,exist_ok=True)

    file_path = os.path.join(patient_folder,uploaded_file.name)

    with open(file_path,"wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success("Report uploaded")

    # --------------------------------------------------
    # FILE TYPE PROCESSING
    # --------------------------------------------------

    if uploaded_file.name.endswith(".pdf"):

        text = extract_pdf_text(file_path)

    elif uploaded_file.name.endswith((".png",".jpg",".jpeg")):

        text = extract_image_text(file_path)

    else:

        with open(file_path,"r") as f:
            text = f.read()


    # --------------------------------------------------
    # ANALYZE REPORT
    # --------------------------------------------------

    with st.spinner("Analyzing report..."):
        summary = analyze_medical_report(text)

    st.markdown("### Report Summary")
    st.markdown(summary)

    rag.index_patient_report(patient_id,text)


# --------------------------------------------------
# CHAT INPUT
# --------------------------------------------------

prompt = st.chat_input("Ask your health question...")

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
            for chunk in ask_question(patient_id, prompt):
                response += chunk
                

            st.markdown(response)

    st.session_state.messages.append({
        "role":"assistant",
        "content":response
    })


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown(
'<div style="position:fixed;bottom:10px;right:20px;color:black;font-size:14px;">Patient Assistance • Local AI + RAG</div>',
unsafe_allow_html=True
)