import mlflow
import numpy as np

def log_live_metrics(prob):
    mlflow.log_metric("live_average_confidence", np.mean(prob))
    mlflow.log_metric("live_prediction_variance", np.var(prob))
