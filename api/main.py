import warnings
# Suppress deprecation warnings from dependencies
# Pydantic v2 warnings (from pandera)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic.*")
# MLflow dependency warnings
warnings.filterwarnings("ignore", message="google.protobuf.service module is deprecated")
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")
warnings.filterwarnings("ignore", category=UserWarning, module="mlflow.*")

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pandas as pd
import time
from prometheus_fastapi_instrumentator import Instrumentator

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

# Add Prometheus metrics instrumentation
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)

# Load model and training data at startup
try:
    model = load_model()
    TRAIN_DF = pd.read_csv("data/training_snapshot.csv")
except Exception as e:
    print(f"Warning: Failed to load model or training data: {e}")
    model = None
    TRAIN_DF = None



class PatientFeatures(BaseModel):
    age: int
    gender: int          # 1 = male, 0 = female
    num_encounters: int
    avg_los: float
    creatinine: float
    heart_rate: float
    systolic_bp: float


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "training_data_loaded": TRAIN_DF is not None
    }

@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint (exposed by instrumentator)."""
    # This is handled by prometheus-fastapi-instrumentator
    pass

@app.post("/predict")
def predict_risk(features: PatientFeatures, request: Request):
    if model is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Model not loaded. Please train the model first.")
    
    if TRAIN_DF is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Training data not loaded. Please train the model first.")
    
    # Convert request payload → DataFrame
    df = pd.DataFrame([features.dict()])

    # 1. Validate schema
    df = patient_feature_schema.validate(df)

    # 2. Feature engineering
    df = prepare_features(df)

    # 3. Drift monitoring (only if we have enough data)
    if len(df) > 0:
        try:
            detect_drift(TRAIN_DF, df)
        except Exception as e:
            # Log but don't fail the request if drift detection fails
            print(f"Drift detection warning: {e}")

    # 4. Prepare features for inference (drop non-feature columns)
    # The model was trained on features after dropping patient_id and readmitted_30d
    feature_cols = [col for col in df.columns if col not in ['patient_id', 'readmitted_30d']]
    df_features = df[feature_cols]

    # 5. Inference
    start_time = time.time()
    dmatrix = xgb.DMatrix(df_features)
    prob = float(model.predict(dmatrix)[0])
    inference_time = time.time() - start_time

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
        "inference_time_ms": round(inference_time * 1000, 2),
        # "explanation": explanation,
        # "clinical_summary": summary,
        # "safety_review": safety_check
    }


