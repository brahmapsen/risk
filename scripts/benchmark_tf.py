import os
import json
import pandas as pd
from glob import glob
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
import mlflow
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.callbacks import EarlyStopping

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
    return df

def run_tensorflow_nn(X, y):
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    # Define simple feedforward model
    # model = tf.keras.Sequential([
    #     tf.keras.layers.Input(shape=(X_train.shape[1],)),   # (3,) features
    #     tf.keras.layers.Dense(8, activation='relu'),
    #     tf.keras.layers.Dense(1, activation='sigmoid')
    # ])

    # Define the model
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(X_train.shape[1],)),  # 3 features
        tf.keras.layers.Dense(8, activation='relu'),
        tf.keras.layers.Dropout(0.1),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])

    model.compile(optimizer='adam',
                  loss='binary_crossentropy',
                  metrics=['accuracy'])

    # Fit model
    # model.fit(X_train, y_train, epochs=10, batch_size=32, verbose=0)

    # Define early stopping
    early_stop = EarlyStopping(
        monitor='val_loss',
        patience=5,
        restore_best_weights=True
    )

    # Train the model
    model.fit(
        X_train, y_train,
        validation_split=0.2,
        epochs=100,
        batch_size=16,
        callbacks=[early_stop],
        verbose=1
    )

    # Evaluate
    y_pred_probs = model.predict(X_test).flatten()
    y_pred = (y_pred_probs > 0.5).astype(int)

    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)

    # Log with MLflow
    with mlflow.start_run(run_name="TensorFlow_NN"):
        mlflow.log_param("model", "TensorFlow_NN")
        mlflow.log_metric("accuracy", acc)
        mlflow.log_metric("f1_score", f1)

    print(f"TensorFlow_NN - Accuracy: {acc:.3f}, F1: {f1:.3f}")

if __name__ == "__main__":
    os.makedirs("models", exist_ok=True)
    mlflow.set_experiment("fhir_benchmark_tensorflow")

    df = load_dataset()
    print("Got dataframe...")
    print("df.shape:", df.shape)
    
    # TensorFlow NN benchmarking
    X = df.drop(columns=["patient_id", "readmission"])
    y = df["readmission"]
    print("X.shape:", X.shape)
    print(df.head())

    run_tensorflow_nn(X, y)
