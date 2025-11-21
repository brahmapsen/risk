"""
Unit tests for model training and validation.
"""
import pytest
import pandas as pd
import numpy as np
import os
import tempfile
import shutil
from pipeline.model import train_model, load_model
from pipeline.feature_engineering import prepare_features


@pytest.fixture
def sample_data():
    """Generate sample training data."""
    np.random.seed(42)
    n_samples = 100
    
    data = {
        'patient_id': [f'P{i}' for i in range(n_samples)],
        'age': np.random.randint(18, 90, n_samples),
        'gender': np.random.randint(0, 2, n_samples),
        'num_encounters': np.random.randint(1, 10, n_samples),
        'avg_los': np.random.uniform(1, 15, n_samples),
        'creatinine': np.random.uniform(0.5, 3.0, n_samples),
        'heart_rate': np.random.uniform(60, 120, n_samples),
        'systolic_bp': np.random.uniform(100, 180, n_samples),
        'readmitted_30d': np.random.randint(0, 2, n_samples)
    }
    
    df = pd.DataFrame(data)
    return df


@pytest.fixture
def temp_mlruns():
    """Create temporary MLflow tracking directory."""
    temp_dir = tempfile.mkdtemp()
    original_uri = os.environ.get('MLFLOW_TRACKING_URI')
    os.environ['MLFLOW_TRACKING_URI'] = f'file://{temp_dir}'
    
    yield temp_dir
    
    # Cleanup
    if original_uri:
        os.environ['MLFLOW_TRACKING_URI'] = original_uri
    else:
        del os.environ['MLFLOW_TRACKING_URI']
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_train_model_basic(sample_data, temp_mlruns):
    """Test that model training completes without errors."""
    model = train_model(sample_data, tune=False)
    
    assert model is not None
    assert os.path.exists("readmission_model.json")
    assert os.path.exists("data/training_snapshot.csv")


def test_model_metrics_exist(sample_data, temp_mlruns):
    """Test that all expected metrics are logged."""
    import mlflow
    
    mlflow.set_experiment("Readmission Risk Model")
    
    with mlflow.start_run() as run:
        model = train_model(sample_data, tune=False)
        
        # Check that metrics were logged
        run_id = run.info.run_id
        client = mlflow.tracking.MlflowClient()
        metrics = client.get_run(run_id).data.metrics
        
        assert 'AUC' in metrics
        assert 'Accuracy' in metrics
        assert 'Precision' in metrics
        assert 'Recall' in metrics
        assert 'F1' in metrics
        
        # Check that metrics are reasonable
        assert 0 <= metrics['AUC'] <= 1
        assert 0 <= metrics['Accuracy'] <= 1
        assert 0 <= metrics['Precision'] <= 1
        assert 0 <= metrics['Recall'] <= 1
        assert 0 <= metrics['F1'] <= 1


def test_load_model():
    """Test that model can be loaded."""
    if os.path.exists("readmission_model.json"):
        model = load_model()
        assert model is not None
    else:
        pytest.skip("Model file does not exist. Run training first.")


def test_feature_engineering(sample_data):
    """Test that feature engineering works correctly."""
    df = prepare_features(sample_data)
    
    # Check that engineered features exist
    assert 'high_creatinine' in df.columns
    assert 'high_bp' in df.columns
    assert 'tachycardia' in df.columns
    assert 'encounter_los_ratio' in df.columns
    
    # Check that original features are still present
    assert 'age' in df.columns
    assert 'creatinine' in df.columns

