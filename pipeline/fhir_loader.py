import json
import glob
import pandas as pd
from datetime import datetime

def load_fhir_bundles(path="./data/fhir/*.json"):
    bundles = []
    for file in glob.glob(path):
        with open(file) as f:
            bundles.append(json.load(f))
    return bundles


def bundle_to_features(bundle):
    patient_id = None
    age = None
    gender = None
    encounters = []
    labs = {}

    for entry in bundle["entry"]:
        resource = entry["resource"]

        if resource["resourceType"] == "Patient":
            patient_id = resource["id"]
            gender = resource.get("gender", "")
            birth_year = int(resource["birthDate"].split("-")[0])
            age = 2024 - birth_year

        if resource["resourceType"] == "Encounter":
            start = resource["period"]["start"]
            end = resource["period"]["end"]
            los = (datetime.fromisoformat(end) - datetime.fromisoformat(start)).days
            encounters.append(los)

        if resource["resourceType"] == "Observation":
            code = resource["code"]["text"]
            value = resource["valueQuantity"]["value"]
            labs[code] = value

    return {
        "patient_id": patient_id,
        "age": age,
        "gender": 1 if gender == "male" else 0,
        "num_encounters": len(encounters),
        "avg_los": sum(encounters) / len(encounters),
        "creatinine": labs.get("creatinine", None),
        "heart_rate": labs.get("heart_rate", None),
        "systolic_bp": labs.get("systolic_bp", None),
        "readmitted_30d": bundle["readmission_label"]
    }


def build_dataset():
    bundles = load_fhir_bundles()
    rows = [bundle_to_features(b) for b in bundles]
    return pd.DataFrame(rows)
