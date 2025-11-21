import mlflow
import numpy as np
import os


def log_live_metrics(prob):
    """Log live prediction metrics to MLflow. Fails gracefully if MLflow is not configured."""
    try:
        # Only log if MLflow tracking URI is properly configured
        tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "./mlruns")
        
        # Ensure mlruns directory exists
        mlruns_dir = tracking_uri.replace("file://", "").replace("./", "")
        if not os.path.exists(mlruns_dir):
            os.makedirs(mlruns_dir, exist_ok=True)
        
        # Set or create Default experiment
        try:
            mlflow.set_experiment("Default")
        except Exception:
            # Create experiment if it doesn't exist
            try:
                mlflow.create_experiment("Default")
                mlflow.set_experiment("Default")
            except Exception:
                # If we can't create experiment, skip logging
                return
        
        # Start a run if none is active
        active_run = mlflow.active_run()
        if active_run is None:
            mlflow.start_run(run_name=f"live-metrics", nested=False)
        
        # Log metrics
        mlflow.log_metric("live_average_confidence", float(np.mean(prob)))
        mlflow.log_metric("live_prediction_variance", float(np.var(prob)))
        
        # End the run
        mlflow.end_run()
            
    except Exception as e:
        # Fail gracefully - don't break the API if MLflow logging fails
        print(f"Warning: Could not log metrics to MLflow: {e}")
        # Ensure we end any active run to avoid leaving it open
        try:
            mlflow.end_run()
        except Exception:
            pass
