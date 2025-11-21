#!/usr/bin/env python3

"""
run.py
---------
This script loads FHIR bundles, converts them to a Pandas dataset,
and trains the readmission prediction model.

Usage:
    python run.py
"""

from pipeline.fhir_loader import build_dataset
from pipeline.model import train_model

def main():
    print("📥 Building dataset from FHIR bundles...")
    df = build_dataset()
    print(f"✔ Dataset loaded. Shape: {df.shape}")

    print("🤖 Training readmission risk model...")
    train_model(df, tune=True)

    print("🎉 Model training completed, model saved!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("❌ Error during execution:", e)
        raise
