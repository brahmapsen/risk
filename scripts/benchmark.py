import os
import json
import pandas as pd
import numpy as np
from glob import glob
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
import mlflow
import joblib

FHIR_DIR = "data/fhir"

def flatten_fhir(filepath):
    with open(filepath) as f:
        data = json.load(f)

    patient_id = data["entry"][0]["resource"]["id"]
    label = int(data.get("readmission_label", False))

    obs = {}
    for entry in data["entry"]:
        resource = entry["resource"]
        if resource["resourceType"] == "Observation":
            code = resource["code"]["text"]
            val = resource["valueQuantity"]["value"]
            obs[code] = val

    return {"patient_id": patient_id, "readmission": label, **obs}

def load_dataset():
    print("Loading dataset from FHIR files...")
    files = glob(os.path.join(FHIR_DIR, "*.json"))
    rows = [flatten_fhir(f) for f in files]
    df = pd.DataFrame(rows).fillna(0)
    print("Returning dataframe...")
    return df

def benchmark_models(df):
    X = df.drop(columns=["patient_id", "readmission"])
    y = df["readmission"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, random_state=42)

    models = {
        "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42),
        "GradientBoosting": GradientBoostingClassifier(random_state=42),
        "LogisticRegression": LogisticRegression(max_iter=1000)
    }

    for name, model in models.items():
        with mlflow.start_run(run_name=name):
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            acc = accuracy_score(y_test, preds)
            f1 = f1_score(y_test, preds)

            mlflow.log_param("model", name)
            mlflow.log_metric("accuracy", acc)
            mlflow.log_metric("f1_score", f1)

            joblib.dump(model, f"models/{name}.joblib")
            mlflow.log_artifact(f"models/{name}.joblib")

            print(f"{name} - Accuracy: {acc:.3f}, F1: {f1:.3f}")

if __name__ == "__main__":
    os.makedirs("models", exist_ok=True)
    mlflow.set_experiment("fhir_benchmark")
    df = load_dataset()
    benchmark_models(df)
