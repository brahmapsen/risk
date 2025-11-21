import pandas as pd
import numpy as np


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add new columns that are derived from raw FHIR features.
    """

    # Example: creatinine flags for kidney injury
    df["high_creatinine"] = (df["creatinine"] > 1.5).astype(int)

    # Blood pressure category
    df["high_bp"] = (df["systolic_bp"] >= 140).astype(int)

    # Tachycardia indicator
    df["tachycardia"] = (df["heart_rate"] >= 100).astype(int)

    # Encounter frequency per LOS ratio
    df["encounter_los_ratio"] = df["num_encounters"] / (df["avg_los"] + 1e-6)

    return df


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fill missing values using simple logic. 
    (In real-world pipelines, this can be replaced with advanced imputation.)
    """

    numeric_cols = df.select_dtypes(include=[np.number]).columns

    for col in numeric_cols:
        df[col] = df[col].fillna(df[col].median())

    return df


def encode_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure categorical fields are properly encoded.
    Gender is already encoded (1=male, 0=female), but this function
    prepares you for adding ethnicity, insurance type, etc. later.
    """

    # Placeholder for future expansion
    return df


def normalize_features(df: pd.DataFrame, exclude=None) -> pd.DataFrame:
    """
    Optional: Normalize numerical columns (not required for XGBoost).
    """

    if exclude is None:
        exclude = []

    numeric_cols = [col for col in df.columns if col not in exclude and df[col].dtype != "object"]

    for col in numeric_cols:
        df[col] = (df[col] - df[col].mean()) / (df[col].std() + 1e-6)

    return df


def prepare_features(df: pd.DataFrame, normalize=False) -> pd.DataFrame:
    """
    Master function. Call this before training or predicting.
    """

    df = df.copy()

    # Step 1: Handle missing values
    df = handle_missing_values(df)

    # Step 2: Add derived clinical features
    df = add_derived_features(df)

    # Step 3: Encode categoricals
    df = encode_categoricals(df)

    # OPTIONAL Step 4: Normalize numerical features
    if normalize:
        df = normalize_features(df, exclude=["readmitted_30d", "patient_id"])

    return df
