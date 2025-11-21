import json
import os
import random
import uuid
from datetime import datetime, timedelta

OUTPUT_DIR = "./data/fhir/"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_patient():
    patient_id = str(uuid.uuid4())
    birth_year = random.randint(1950, 2005)
    gender = random.choice(["male", "female"])

    return {
        "resourceType": "Patient",
        "id": patient_id,
        "gender": gender,
        "birthDate": f"{birth_year}-01-01"
    }, patient_id


def generate_encounters(patient_id):
    """Generates 1–3 encounters and flags a 30-day readmission."""
    encounters = []
    base_date = datetime(2024, 1, 1)

    num_encounters = random.randint(1, 3)
    readmission_flag = False

    for i in range(num_encounters):
        admit = base_date + timedelta(days=random.randint(0, 200))
        discharge = admit + timedelta(days=random.randint(2, 7))

        encounter_id = str(uuid.uuid4())

        encounters.append({
            "resourceType": "Encounter",
            "id": encounter_id,
            "subject": {"reference": f"Patient/{patient_id}"},
            "period": {
                "start": admit.isoformat(),
                "end": discharge.isoformat()
            }
        })

        if i > 0:
            prev_end = datetime.fromisoformat(encounters[i-1]["period"]["end"])
            if (admit - prev_end).days <= 30:
                readmission_flag = True

    return encounters, readmission_flag


def generate_observations(patient_id):
    """Vitals + labs."""
    observations = []

    # Example observation fields
    vitals = {
        "heart_rate": random.randint(60, 120),
        "systolic_bp": random.randint(90, 180),
        "creatinine": round(random.uniform(0.6, 3.0), 2),
    }

    for name, value in vitals.items():
        observations.append({
            "resourceType": "Observation",
            "id": str(uuid.uuid4()),
            "subject": {"reference": f"Patient/{patient_id}"},
            "code": {"text": name},
            "valueQuantity": {"value": value}
        })

    return observations


def main(n=200):
    for _ in range(n):
        patient, patient_id = generate_patient()
        encounters, readmission = generate_encounters(patient_id)
        observations = generate_observations(patient_id)

        bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "readmission_label": readmission,
            "entry": [{"resource": patient}]
                     + [{"resource": e} for e in encounters]
                     + [{"resource": o} for o in observations]
        }

        with open(os.path.join(OUTPUT_DIR, f"{patient_id}.json"), "w") as f:
            json.dump(bundle, f, indent=2)

    print("Generated synthetic FHIR bundles.")

if __name__ == "__main__":
    main()
