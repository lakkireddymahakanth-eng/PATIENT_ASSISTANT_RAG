from src.core.rag_engine import RAGEngine
from src.services.patient_service import load_patient, patient_to_context
from src.core.safety import check_emergency
import ollama


def ask_question(patient_id: str, question: str, chat_history=None):

    if chat_history is None:
        chat_history = []

    if check_emergency(question):
        yield "⚠️ This may be a medical emergency. Please contact a doctor immediately."
        return

    rag = RAGEngine()

    patient = load_patient(patient_id)

    if patient is None:
        yield f"Patient ID {patient_id} not found."
        return

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
You are a medical support assistant.

PATIENT INFORMATION:
{patient_context}

MEDICAL GUIDELINES AND REPORTS:
{docs_context}

CHAT HISTORY:
{history_text}

Relevant Sources:
{sources_text}

QUESTION:
{question}

Provide a helpful and safe response.
"""

    stream = ollama.chat(
        model="llama3",
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    for chunk in stream:
        yield chunk["message"]["content"]