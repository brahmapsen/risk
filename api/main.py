from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd

from pipeline.model import load_model
from pipeline.feature_engineering import prepare_features

from pipeline.schema.data_schema import patient_feature_schema

from pipeline.monitor.lineage import log_lineage
from pipeline.monitor.model_health import log_live_metrics
from pipeline.monitor.drift import detect_drift

from pipeline.llm.llm_utils import (
    explain_prediction,
    explain_drift,
    generate_clinical_summary,
    safety_guardrails
)


import xgboost as xgb

app = FastAPI(title="Readmission Risk Predictor")
model = load_model()
TRAIN_DF = pd.read_csv("data/training_snapshot.csv")



class PatientFeatures(BaseModel):
    age: int
    gender: int          # 1 = male, 0 = female
    num_encounters: int
    avg_los: float
    creatinine: float
    heart_rate: float
    systolic_bp: float


@app.post("/predict")
def predict_risk(features: PatientFeatures):
    
    # Convert request payload → DataFrame
    df = pd.DataFrame([features.dict()])

    # 1. Validate schema
    df = patient_feature_schema.validate(df)

    # 2. Feature engineering
    df = prepare_features(df)

    # 3. Drift monitoring
    detect_drift(TRAIN_DF, df)

    # 4. Inference
    dmatrix = xgb.DMatrix(df)
    prob = float(model.predict(dmatrix)[0])

    # LLM explanation
    # explanation = explain_prediction(features.dict(), prob)

    #  Summary
    # summary = generate_clinical_summary(features.dict(), prob)

    #  Safety check
    # safety_check = safety_guardrails(features.dict())

    #  Log lineage + live model health
    log_lineage(features.dict(), prob, model_version="v1")
    log_live_metrics(prob)

    return {
        "probability": prob,
        "risk_level": "High" if prob > 0.5 else "Low",
        # "explanation": explanation,
        # "clinical_summary": summary,
        # "safety_review": safety_check
    }


