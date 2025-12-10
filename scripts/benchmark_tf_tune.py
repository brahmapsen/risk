import optuna
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from pipeline.fhir_loader import build_dataset
from pipeline.feature_engineering import prepare_features

# Load and prepare data
df = build_dataset()
df = prepare_features(df)

X = df.drop(["patient_id", "readmitted_30d"], axis=1)
y = df["readmitted_30d"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)


def objective(trial):
    # Hyperparameters to tune
    n_units = trial.suggest_int('n_units', 4, 64)
    dropout_rate = trial.suggest_float('dropout_rate', 0.1, 0.5)
    learning_rate = trial.suggest_float('learning_rate', 1e-4, 1e-2, log=True)
    batch_size = trial.suggest_categorical('batch_size', [8, 16, 32])
    epochs = trial.suggest_int('epochs', 10, 100)

    # Model
    model = Sequential([
        tf.keras.Input(shape=(X_train.shape[1],)),
        Dense(n_units, activation='relu'),
        Dropout(dropout_rate),
        Dense(1, activation='sigmoid')
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
        loss='binary_crossentropy',
        metrics=['accuracy']
    )

    # Early stopping
    early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)

    # Train
    model.fit(
        X_train, y_train,
        validation_split=0.2,
        epochs=epochs,
        batch_size=batch_size,
        callbacks=[early_stop],
        verbose=0
    )

    # Predict and evaluate
    y_pred = (model.predict(X_test) > 0.5).astype("int32")
    acc = accuracy_score(y_test, y_pred)
    return acc


if __name__ == "__main__":
    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=20)

    print("Best trial:")
    print("  Value (accuracy):", study.best_value)
    print("  Params:")
    for key, value in study.best_params.items():
        print(f"    {key}: {value}")
