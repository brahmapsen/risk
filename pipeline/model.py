import mlflow
import mlflow.xgboost
import xgboost as xgb
import pandas as pd
import os

from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score, f1_score

from pipeline.tuning import tune_hyperparams
from pipeline.feature_engineering import prepare_features

MODEL_PATH = "readmission_model.json"
TRAINING_SNAPSHOT_PATH = "data/training_snapshot.csv"

def train_model(df, tune=True):
    """Train XGBoost model with optional hyperparameter tuning and MLflow logging."""

    # -----------------------------
    # 0. Feature Engineering
    # -----------------------------
    df = prepare_features(df)

    X = df.drop(["patient_id", "readmitted_30d"], axis=1)
    y = df["readmitted_30d"]

    os.makedirs("data", exist_ok=True)

    mlflow.set_experiment("Readmission Risk Model")

    with mlflow.start_run():

        # -----------------------------
        # 1. Hyperparameter Tuning
        # -----------------------------
        if tune:
            best_params = tune_hyperparams(X, y, n_trials=25)
        else:
            best_params = {
                "objective": "binary:logistic",
                "eval_metric": "auc",
                "eta": 0.1,
                "max_depth": 4,
                "subsample": 0.9
            }

        mlflow.log_params(best_params)

        # -----------------------------
        # 2. Train/Test Split
        # -----------------------------
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # -----------------------------
        # NEW: Save Training Snapshot
        # -----------------------------
        training_snapshot = X_train.copy()
        training_snapshot["readmitted_30d"] = y_train.values

        training_snapshot.to_csv(TRAINING_SNAPSHOT_PATH, index=False)
        mlflow.log_artifact(TRAINING_SNAPSHOT_PATH)

        print(f"Training snapshot saved to {TRAINING_SNAPSHOT_PATH}")

        # -----------------------------
        # 3. Train Booster
        # -----------------------------
        dtrain = xgb.DMatrix(X_train, label=y_train)
        dtest = xgb.DMatrix(X_test, label=y_test)

        model = xgb.train(
            params=best_params,
            dtrain=dtrain,
            num_boost_round=200
        )

        # -----------------------------
        # 4. Evaluation Metrics
        # -----------------------------
        preds = model.predict(dtest)
        preds_binary = (preds > 0.5).astype(int)
        
        auc = roc_auc_score(y_test, preds)
        acc = accuracy_score(y_test, preds_binary)
        precision = precision_score(y_test, preds_binary)
        recall = recall_score(y_test, preds_binary)
        f1 = f1_score(y_test, preds_binary)

        mlflow.log_metric("AUC", auc)
        mlflow.log_metric("Accuracy", acc)
        mlflow.log_metric("Precision", precision)
        mlflow.log_metric("Recall", recall)
        mlflow.log_metric("F1", f1)

        print(f"AUC: {auc:.4f}, Accuracy: {acc:.4f}, Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1:.4f}")

        # -----------------------------
        # 5. Save Model
        # -----------------------------
        model.save_model(MODEL_PATH)
        mlflow.log_artifact(MODEL_PATH)

        print(f"Model saved to {MODEL_PATH}")

        return model

def load_model():
    """Load the trained XGBoost Booster model."""
    booster = xgb.Booster()
    booster.load_model(MODEL_PATH)
    return booster
