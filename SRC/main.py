from core.rag_engine import RAGEngine
from services.patient_service import load_patient, patient_to_context
from core.safety import check_emergency
import ollama


def ask_question(patient_id: str, question: str):

    if check_emergency(question):
        yield "⚠️ This may be a medical emergency. Please contact a doctor immediately."
        return

    rag = RAGEngine()

    patient_context = ""

    # Load patient info only if ID is provided
    if patient_id:
        patient = load_patient(patient_id)

        if patient:
            patient_context = patient_to_context(patient)

    retrieved_docs = rag.retrieve(question)
    docs_context = "\n\n".join(retrieved_docs)

    prompt = f"""
You are a medical support assistant.

If patient information is available, use it.
If not, answer generally.

PATIENT INFORMATION:
{patient_context}

MEDICAL GUIDELINES:
{docs_context}

QUESTION:
{question}
"""

    response = ollama.chat(
        model="llama3",
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    for chunk in response:
        yield chunk["message"]["content"]