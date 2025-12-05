## A predictive intelligence layer 
for hospitals that continuously analyzes patient, operational, and staffing data to flag emerging risks before they become adverse events.

AI-powered hospital risk command center that predicts patient deterioration, readmissions, and operational bottlenecks before they happen — and gives clinicians actionable insights in real time.

hlth/cip/risk

# generate synthetic data in the data/fhir directory.
python scripts/generate_data.py 

## build ML dataset
python run.py

# Run API to predict for a scenario
uvicorn api.main:app --reload

## Test 
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
        "age": 72,
        "gender": 1,
        "num_encounters": 2,
        "avg_los": 4.5,
        "creatinine": 1.8,
        "heart_rate": 110,
        "systolic_bp": 145
      }'


# START ML-FLOW
hlth/cip/risk

mlflow ui
localhost:5000

## Docker Deployment

# Build and run with Docker Compose
docker build -t readmission-risk-api:local .

# With monitoring (Prometheus + Grafana)
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# Test for data drifting
python pipeline/monitor/test_drift.py

# View services
# API: http://localhost:8000
# MLflow UI: http://localhost:5000
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)

## Deployment


## CI/CD

The project includes a complete CI/CD pipeline:
- Automated testing and validation
- Docker image building
- Model registry integration
- Staging and production deployment

