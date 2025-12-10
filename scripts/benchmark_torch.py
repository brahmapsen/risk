import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import mlflow
import mlflow.pytorch

from pipeline.fhir_loader import build_dataset
from pipeline.feature_engineering import prepare_features

# Define the PyTorch model
class ReadmissionNN(nn.Module):
    def __init__(self, input_dim):
        super(ReadmissionNN, self).__init__()
        self.model = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.model(x)

def train_and_evaluate():
    df = build_dataset()
    df = prepare_features(df)

    X = df.drop(columns=["patient_id", "readmitted_30d"])
    y = df["readmitted_30d"]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42
    )

    # Convert to PyTorch tensors
    X_train_tensor = torch.tensor(X_train, dtype=torch.float32)
    y_train_tensor = torch.tensor(y_train.values, dtype=torch.float32).view(-1, 1)
    X_test_tensor = torch.tensor(X_test, dtype=torch.float32)
    y_test_tensor = torch.tensor(y_test.values, dtype=torch.float32).view(-1, 1)

    input_dim = X_train.shape[1]
    model = ReadmissionNN(input_dim)
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    mlflow.set_experiment("PyTorch Readmission Benchmark")
    with mlflow.start_run():
        mlflow.log_param("optimizer", "Adam")
        mlflow.log_param("loss", "BCELoss")
        mlflow.log_param("lr", 0.001)
        mlflow.log_param("batch_size", 32)
        mlflow.log_param("epochs", 50)

        for epoch in range(50):
            model.train()
            optimizer.zero_grad()
            outputs = model(X_train_tensor)
            loss = criterion(outputs, y_train_tensor)
            loss.backward()
            optimizer.step()

            if epoch % 10 == 0:
                print(f"Epoch {epoch}: Loss = {loss.item():.4f}")

        # Evaluation
        model.eval()
        with torch.no_grad():
            preds = model(X_test_tensor)
            preds_labels = (preds >= 0.5).float()

        acc = accuracy_score(y_test_tensor, preds_labels)
        f1 = f1_score(y_test_tensor, preds_labels)

        mlflow.log_metric("accuracy", acc)
        mlflow.log_metric("f1_score", f1)
        mlflow.pytorch.log_model(model, "model")

        print(f"PyTorch - Accuracy: {acc:.3f}, F1: {f1:.3f}")


if __name__ == "__main__":
    train_and_evaluate()
