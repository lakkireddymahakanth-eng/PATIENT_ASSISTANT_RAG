
print("Generating synthetic patient data...")

import json
import random
from datetime import datetime, timedelta



first_names = [
    "John", "Anita", "David", "Maria", "Rahul", "Sophia", "Michael",
    "Emma", "Daniel", "Olivia", "James", "Ava", "William", "Mia",
    "Alexander", "Charlotte", "Ethan", "Amelia", "Benjamin", "Harper"
]

last_names = [
    "Smith", "Sharma", "Kim", "Lopez", "Mehta", "Brown",
    "Garcia", "Johnson", "Patel", "Wilson", "Martinez", "Taylor"
]

conditions_data = {
    "Type 2 Diabetes": {
        "medications": ["Metformin 500mg twice daily"],
        "diet": "Low sugar diet. Avoid sweets and refined carbohydrates.",
        "notes": "Blood glucose slightly elevated. Monitor fasting sugar daily."
    },
    "Hypertension": {
        "medications": ["Lisinopril 10mg daily"],
        "diet": "Low sodium diet. Avoid processed and salty foods.",
        "notes": "Blood pressure moderately elevated."
    },
    "Post Appendectomy": {
        "medications": ["Ibuprofen 400mg as needed"],
        "diet": "Soft foods for 2-3 weeks. Avoid spicy and fried items.",
        "notes": "Surgical incision healing normally."
    },
    "Coronary Artery Disease": {
        "medications": ["Aspirin 75mg daily", "Atorvastatin 20mg nightly"],
        "diet": "Low cholesterol diet. Increase vegetables and whole grains.",
        "notes": "Stable cardiac status."
    },
    "Asthma": {
        "medications": ["Salbutamol inhaler as needed"],
        "diet": "Avoid allergens and cold beverages.",
        "notes": "Mild wheezing observed."
    }
}

def random_date():
    return (datetime.now() + timedelta(days=random.randint(7, 90))).strftime("%Y-%m-%d")

patients = []

for i in range(1, 61):  # 60 patients
    condition = random.choice(list(conditions_data.keys()))
    data = conditions_data[condition]

    patient = {
        "id": f"P{str(i).zfill(3)}",
        "name": f"{random.choice(first_names)} {random.choice(last_names)}",
        "age": random.randint(25, 75),
        "condition": condition,
        "allergies": random.choice([[], ["Penicillin"], ["Dust"], ["Peanuts"]]),
        "medications": data["medications"],
        "last_visit": {
            "doctor_notes": data["notes"],
            "diet_plan": data["diet"],
            "follow_up": random_date()
        }
    }

    patients.append(patient)

with open("data/patients.json", "w") as f:
    json.dump(patients, f, indent=2)

print("✅ 60 synthetic patients generated successfully!")
