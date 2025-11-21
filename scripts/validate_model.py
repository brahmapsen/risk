#!/usr/bin/env python3
"""
Model validation script for CI/CD.
Checks that model metrics meet minimum thresholds.
"""
import mlflow
import sys
import os

# Minimum acceptable metrics thresholds
METRIC_THRESHOLDS = {
    "AUC": 0.70,      # Minimum AUC of 0.70
    "Accuracy": 0.65,  # Minimum Accuracy of 0.65
    "Precision": 0.60, # Minimum Precision of 0.60
    "Recall": 0.60,    # Minimum Recall of 0.60
    "F1": 0.60         # Minimum F1 of 0.60
}


def get_latest_run_metrics(experiment_name="Readmission Risk Model"):
    """Get metrics from the most recent MLflow run."""
    try:
        mlflow.set_experiment(experiment_name)
        
        # Get the experiment
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment is None:
            print(f"❌ Experiment '{experiment_name}' not found")
            return None
        
        # Get all runs for this experiment
        client = mlflow.tracking.MlflowClient()
        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=["start_time DESC"],
            max_results=1
        )
        
        if not runs:
            print(f"❌ No runs found in experiment '{experiment_name}'")
            return None
        
        latest_run = runs[0]
        return latest_run.data.metrics
        
    except Exception as e:
        print(f"❌ Error retrieving metrics: {e}")
        return None


def validate_metrics(metrics):
    """Validate that all metrics meet thresholds."""
    if metrics is None:
        return False
    
    all_passed = True
    
    print("\n📊 Model Validation Results:")
    print("=" * 50)
    
    for metric_name, threshold in METRIC_THRESHOLDS.items():
        if metric_name not in metrics:
            print(f"❌ {metric_name}: NOT FOUND")
            all_passed = False
            continue
        
        value = metrics[metric_name]
        passed = value >= threshold
        
        status = "✅" if passed else "❌"
        print(f"{status} {metric_name}: {value:.4f} (threshold: {threshold:.2f})")
        
        if not passed:
            all_passed = False
    
    print("=" * 50)
    
    return all_passed


def main():
    """Main validation function."""
    # Set MLflow tracking URI if not set
    if "MLFLOW_TRACKING_URI" not in os.environ:
        os.environ["MLFLOW_TRACKING_URI"] = "./mlruns"
    
    print("🔍 Validating model metrics...")
    
    metrics = get_latest_run_metrics()
    
    if metrics is None:
        print("\n❌ Failed to retrieve metrics. Make sure you've trained a model.")
        sys.exit(1)
    
    if validate_metrics(metrics):
        print("\n✅ All metrics meet the required thresholds!")
        sys.exit(0)
    else:
        print("\n❌ Some metrics do not meet the required thresholds.")
        print("   Model validation failed. Please improve the model before deploying.")
        sys.exit(1)


if __name__ == "__main__":
    main()

