# Deployment Guide

This guide covers deploying the Readmission Risk Predictor API to cloud environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Monitoring Setup](#monitoring-setup)
6. [Model Registry](#model-registry)
7. [Secrets Management](#secrets-management)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

- Python 3.12+
- Docker and Docker Compose
- MLflow (for model tracking)
- Access to cloud provider (AWS, GCP, Azure, etc.)
- GitHub repository with Actions enabled

## Local Development Setup

### 1. Clone and Setup

```bash
git clone <repository-url>
cd risk
source env/bin/activate  # or create virtual environment
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

Required environment variables:
- `AIML_API_KEY`: Your AIML API key for LLM features
- `MLFLOW_TRACKING_URI`: MLflow tracking URI (default: `./mlruns`)

### 3. Generate Data and Train Model

```bash
# Generate synthetic data
python scripts/generate_data.py

# Train the model
python run.py
```

### 4. Run API Locally

```bash
uvicorn api.main:app --reload
```

API will be available at `http://localhost:8000`

## Docker Deployment

### Build and Run with Docker Compose

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Services

- **API**: `http://localhost:8000`
- **MLflow UI**: `http://localhost:5000`

### With Monitoring

```bash
# Start with Prometheus and Grafana
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

Additional services:
- **Prometheus**: `http://localhost:9090`
- **Grafana**: `http://localhost:3000` (admin/admin)

## Cloud Deployment

### Option 1: AWS (EC2/ECS/EKS)

#### EC2 Deployment

1. **Launch EC2 Instance**
   ```bash
   # SSH into instance
   ssh -i your-key.pem ec2-user@your-instance-ip
   ```

2. **Install Docker**
   ```bash
   sudo yum update -y
   sudo yum install docker -y
   sudo systemctl start docker
   sudo usermod -aG docker ec2-user
   ```

3. **Deploy Application**
   ```bash
   git clone <repository-url>
   cd risk
   docker-compose up -d
   ```

#### ECS Deployment

1. **Build and Push Docker Image**
   ```bash
   docker build -t readmission-risk-api .
   docker tag readmission-risk-api:latest <your-ecr-repo>/readmission-risk-api:latest
   docker push <your-ecr-repo>/readmission-risk-api:latest
   ```

2. **Create ECS Task Definition** (see `deployment/ecs-task-definition.json`)

3. **Deploy to ECS**
   ```bash
   aws ecs update-service --cluster your-cluster --service readmission-api --force-new-deployment
   ```

### Option 2: Google Cloud Platform (GCP)

#### Cloud Run Deployment

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT_ID/readmission-risk-api

# Deploy to Cloud Run
gcloud run deploy readmission-risk-api \
  --image gcr.io/PROJECT_ID/readmission-risk-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Option 3: Azure

#### Container Instances

```bash
# Build and push to ACR
az acr build --registry <registry-name> --image readmission-risk-api:latest .

# Deploy to Container Instances
az container create \
  --resource-group <resource-group> \
  --name readmission-api \
  --image <registry-name>.azurecr.io/readmission-risk-api:latest \
  --cpu 2 --memory 4
```

### Option 4: Kubernetes

1. **Create Kubernetes Manifests** (see `deployment/k8s/` directory)

2. **Deploy**
   ```bash
   kubectl apply -f deployment/k8s/
   ```

3. **Check Status**
   ```bash
   kubectl get pods
   kubectl get services
   ```

## Monitoring Setup

### Prometheus Metrics

The API automatically exposes Prometheus metrics at `/metrics`.

Key metrics:
- `http_request_duration_seconds`: Request latency
- `http_requests_total`: Request count
- `http_request_size_bytes`: Request size

### Grafana Dashboards

1. Access Grafana: `http://localhost:3000`
2. Login: `admin` / `admin` (change on first login)
3. Prometheus datasource is pre-configured
4. Import dashboard or create custom dashboards

### Health Checks

- **Health Endpoint**: `GET /health`
- **Metrics Endpoint**: `GET /metrics`

## Model Registry

### MLflow Model Registry

Models are automatically registered in MLflow Model Registry after training.

#### View Models

```bash
# Start MLflow UI
mlflow ui

# Or via Docker
docker-compose up mlflow
```

Access at `http://localhost:5000`

#### Model Stages

- **Staging**: Models that meet minimum thresholds but not production-ready
- **Production**: Models with AUC ≥ 0.75 and F1 ≥ 0.65

#### Load Model from Registry

The API automatically loads models from the registry:

```python
from pipeline.model import load_model

# Load production model
model = load_model(stage="Production")

# Load staging model
model = load_model(stage="Staging")

# Load latest version
model = load_model(stage=None)
```

## Secrets Management

### GitHub Secrets

For CI/CD, configure secrets in GitHub:

1. Go to: Repository → Settings → Secrets and variables → Actions
2. Add the following secrets:
   - `AIML_API_KEY`: Your AIML API key
   - `DOCKER_REGISTRY`: Docker registry URL
   - `DOCKER_USERNAME`: Docker registry username
   - `DOCKER_PASSWORD`: Docker registry password/token
   - `STAGING_URL`: Staging environment URL
   - `PRODUCTION_URL`: Production environment URL

### Local Development

Create `.env` file:

```bash
cp .env.example .env
# Edit .env with your values
```

### Cloud Secrets

#### AWS Secrets Manager

```bash
aws secretsmanager create-secret \
  --name readmission-api/secrets \
  --secret-string file://secrets.json
```

#### GCP Secret Manager

```bash
gcloud secrets create aiml-api-key --data-file=-
echo -n "your-api-key" | gcloud secrets versions add aiml-api-key --data-file=-
```

#### Azure Key Vault

```bash
az keyvault secret set \
  --vault-name <vault-name> \
  --name "AIML-API-KEY" \
  --value "your-api-key"
```

## CI/CD Pipeline

The GitHub Actions workflow automatically:

1. **Lint and Test**: Runs code quality checks and tests
2. **Model Validation**: Trains model and validates metrics
3. **API Testing**: Tests API endpoints
4. **Build Docker Image**: Builds and pushes to registry (on main branch)
5. **Deploy to Staging**: Auto-deploys to staging (on push to main)
6. **Deploy to Production**: Manual deployment via workflow_dispatch

### Manual Production Deployment

1. Go to: Actions → CI/CD Pipeline → Run workflow
2. Select branch: `main`
3. Click "Run workflow"

## Troubleshooting

### Model Not Loading

```bash
# Check if model file exists
ls -la readmission_model.json

# Check MLflow registry
mlflow models list

# Train model if missing
python run.py
```

### API Not Starting

```bash
# Check logs
docker-compose logs api

# Check environment variables
docker-compose exec api env

# Verify model and data files
docker-compose exec api ls -la /app/data/
```

### Monitoring Not Working

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check API metrics endpoint
curl http://localhost:8000/metrics

# Verify Grafana datasource
# Go to Grafana → Configuration → Data Sources
```

### Docker Build Fails

```bash
# Clean build
docker-compose build --no-cache

# Check Dockerfile syntax
docker build -t test .
```

## Production Checklist

Before deploying to production:

- [ ] All tests passing
- [ ] Model metrics meet thresholds
- [ ] Environment variables configured
- [ ] Secrets properly secured
- [ ] Monitoring set up
- [ ] Health checks configured
- [ ] Backup strategy in place
- [ ] Logging configured
- [ ] SSL/TLS certificates configured
- [ ] Rate limiting configured (if needed)
- [ ] Documentation updated

## Support

For issues or questions:
- Check logs: `docker-compose logs -f`
- Review MLflow UI: `http://localhost:5000`
- Check Prometheus: `http://localhost:9090`
- Review GitHub Actions: Repository → Actions

