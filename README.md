## A predictive intelligence layer 
for hospitals that continuously analyzes patient, operational, and staffing data to flag emerging risks before they become adverse events.

AI-powered hospital risk command center that predicts patient deterioration, readmissions, and operational bottlenecks before they happen — and gives clinicians actionable insights in real time.

hlth/cip/risk
source env/bin/activate

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
source env/bin/activate
mlflow ui
localhost:5000

