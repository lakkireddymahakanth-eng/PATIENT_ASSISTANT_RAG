import json


def load_patient(patient_id: str):
    with open("data/patients.json", "r") as f:
        patients = json.load(f)

    for patient in patients:
        if patient["id"] == patient_id:
            return patient

    return None


def patient_to_context(patient: dict) -> str:
    if not patient:
        return "No patient data available."

    return f"""
Patient Name: {patient['name']}
Age: {patient['age']}
Condition: {patient['condition']}
Allergies: {', '.join(patient['allergies']) if patient['allergies'] else 'None'}
Medications: {', '.join(patient['medications'])}

Doctor Notes:
{patient['last_visit']['doctor_notes']}

Diet Plan:
{patient['last_visit']['diet_plan']}

Follow-up Date:
{patient['last_visit']['follow_up']}
""".strip()