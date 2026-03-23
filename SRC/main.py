from src.core.rag_engine import RAGEngine
from src.services.patient_service import load_patient, patient_to_context
from src.core.safety import check_emergency

from src.services.conversation_engine import run_conversation_loop
from src.services.location_service import get_location_details
from src.services.appointment_service import book_appointment
from src.services.medical_history import log_event
from src.services.conversation_history_service import save_conversation

import ollama

rag = RAGEngine()


def ask_question(patient_id: str, question: str, chat_history=None):

    if chat_history is None:
        chat_history = []

    # 🚨 Emergency
    if check_emergency(question):
        yield "🚨 This may be a medical emergency. Please seek immediate help."
        return

    patient = load_patient(patient_id)

    if patient is None:
        yield f"Patient ID {patient_id} not found."
        return

    # -------------------------
    # 📅 Appointment Flow
    # -------------------------
    if "appointment" in question.lower():

        yield "🤖 Starting interactive booking...\n"

        details, history = run_conversation_loop()

        location_data = get_location_details(details["location"])

        if not location_data:
            yield "⚠️ Invalid location"
            return

        appointment = book_appointment(
            patient_id,
            patient,
            location_data,
            details["insurance"],
            details
        )

        save_conversation(patient_id, history)

        log_event(patient_id, "Appointment booked")

        yield f"""
✅ Appointment Confirmed!

👤 Name: {appointment['name']}
📞 Phone: {appointment['phone']}

🩺 Problem: {appointment['problem']}
📝 Notes: {appointment['notes']}

👨‍⚕ Doctor: {appointment['doctor']}
📍 Location: {appointment['location']['address']}

🕒 Time: {appointment['datetime']}
🛡 Insurance: {appointment['insurance']['type']}
"""
        return

    # -------------------------
    # 🧠 RAG FLOW
    # -------------------------
    patient_context = patient_to_context(patient)

    retrieved_docs = rag.retrieve(question)

    docs_context = ""
    sources = []

    for doc in retrieved_docs:
        docs_context += doc["content"] + "\n\n"
        sources.append(doc["source"])

    sources_text = ", ".join(set(sources))

    history_text = ""
    for q, a in chat_history:
        history_text += f"User: {q}\nAssistant: {a}\n"

    prompt = f"""
You are a medical assistant.

RULES:
- Do NOT diagnose
- Do NOT prescribe medication
- Suggest consulting a doctor when needed

PATIENT:
{patient_context}

CONTEXT:
{docs_context}

QUESTION:
{question}
"""

    stream = ollama.chat(
        model="llama3",
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    for chunk in stream:
        yield chunk["message"]["content"]

    yield f"\n\n📚 Sources: {sources_text}"