# CI/CD Pipeline Documentation

This project includes a comprehensive CI/CD pipeline using GitHub Actions.

## Pipeline Overview

The CI/CD pipeline consists of three main jobs:

### 1. Lint and Test (`lint-and-test`)
- **Linting**: Runs `flake8` for code quality checks
- **Formatting**: Checks code formatting with `black`
- **Unit Tests**: Runs pytest with coverage reporting
- **Coverage**: Uploads coverage reports to Codecov

### 2. Model Validation (`model-validation`)
- **Data Generation**: Generates synthetic test data
- **Model Training**: Trains the model using the training pipeline
- **Metric Validation**: Validates that model metrics meet minimum thresholds:
  - AUC ≥ 0.70
  - Accuracy ≥ 0.65
  - Precision ≥ 0.60
  - Recall ≥ 0.60
  - F1 ≥ 0.60

### 3. API Testing (`api-test`)
- **Model Setup**: Generates data and trains model
- **Server Startup**: Starts the FastAPI server
- **Integration Tests**: Tests API endpoints with various scenarios

## Running Tests Locally

### Install test dependencies
```bash
pip install -r requirements.txt
```

### Run all tests
```bash
pytest tests/ -v
```

### Run with coverage
```bash
pytest tests/ -v --cov=pipeline --cov=api --cov-report=term-missing
```

### Run specific test file
```bash
pytest tests/test_model.py -v
pytest tests/test_api.py -v
```

### Validate model metrics
```bash
python scripts/validate_model.py
```

## Adjusting Metric Thresholds

Edit `scripts/validate_model.py` and modify the `METRIC_THRESHOLDS` dictionary:

```python
METRIC_THRESHOLDS = {
    "AUC": 0.70,      # Adjust as needed
    "Accuracy": 0.65,
    "Precision": 0.60,
    "Recall": 0.60,
    "F1": 0.60
}
```

## Workflow Triggers

The pipeline runs automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Manual trigger via GitHub Actions UI (workflow_dispatch)

## Next Steps for Production

1. **Model Registry**: Set up MLflow Model Registry for versioning
2. **Deployment**: Add deployment job to deploy model to staging/production
3. **Monitoring**: Integrate with monitoring tools (e.g., Prometheus, Grafana)
4. **Notifications**: Add Slack/email notifications for failed builds
5. **Secrets Management**: Use GitHub Secrets for API keys and credentials
6. **Docker**: Containerize the application for consistent deployments
7. **Kubernetes**: Deploy to Kubernetes for production scaling

## Troubleshooting

### Tests fail locally
- Ensure you've generated test data: `python scripts/generate_data.py`
- Train a model first: `python run.py`
- Check that all dependencies are installed

### Model validation fails
- Review the metric thresholds in `scripts/validate_model.py`
- Check if the model was trained recently
- Verify MLflow tracking URI is set correctly

### API tests fail
- Ensure the model file exists: `readmission_model.json`
- Check that training snapshot exists: `data/training_snapshot.csv`
- Verify the API server can start: `uvicorn api.main:app`

