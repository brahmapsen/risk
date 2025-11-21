# Deployment Options After Using GHCR

GHCR (GitHub Container Registry) is just where your Docker images are **stored**. You still need to **deploy** those images to a hosting platform.

## Deployment Platforms

### 1. Cloud Platforms (Recommended)

#### AWS
- **EC2**: Virtual server - pull image and run
- **ECS**: Container service - uses your GHCR image
- **EKS**: Kubernetes - deploy from GHCR
- **App Runner**: Fully managed - just point to GHCR image

#### Google Cloud Platform (GCP)
- **Cloud Run**: Serverless containers - pull from GHCR
- **GKE**: Kubernetes - deploy from GHCR
- **Compute Engine**: VM - pull and run container


#### Kubernetes Cluster
- Self-managed K8s
- On-premises or cloud

### Option 1: AWS App Runner (Easiest)
**Why**: Fully managed, just point to GHCR image

**Steps**:
1. Go to AWS App Runner
2. Create service
3. Source: Container registry
4. Image URI: `ghcr.io/your-username/readmission-risk-api:latest`
5. Authentication: Use GitHub token
6. Done!

**Cost**: Pay per request (~$0.007 per vCPU-hour)

### Option 2: Google Cloud Run (Serverless)
**Why**: Serverless, auto-scales, very cheap

**Steps**:
1. Install gcloud CLI
2. Authenticate: `gcloud auth configure-docker ghcr.io`
3. Deploy:
   ```bash
   gcloud run deploy readmission-api \
     --image ghcr.io/your-username/readmission-risk-api:latest \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```
**Cost**: Free tier: 2 million requests/month, then $0.40 per million

## Example: Deploy to Google Cloud Run

```bash
# 1. Install gcloud CLI (if not installed)
# https://cloud.google.com/sdk/docs/install

# 2. Authenticate
gcloud auth login
gcloud auth configure-docker ghcr.io

# 3. Deploy
gcloud run deploy readmission-risk-api \
  --image ghcr.io/YOUR-USERNAME/readmission-risk-api:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 2Gi \
  --cpu 2 \
  --set-env-vars "MLFLOW_TRACKING_URI=./mlruns"

# 4. Get URL
gcloud run services describe readmission-risk-api --region us-central1
```

## Example: Deploy to AWS App Runner

1. Go to AWS Console → App Runner
2. Create service
3. Source: Container registry
4. Provider: Other
5. Container image URI: `ghcr.io/your-username/readmission-risk-api:latest`
6. Authentication: Create new access role with GHCR token
7. Port: 8000
8. Deploy!


## Next Steps

1. **Choose a platform** from above
2. **Update deployment job** in `.github/workflows/ci.yml` with platform-specific commands
3. **Set up environment variables** on your chosen platform
4. **Deploy!**

Want help setting up a specific platform? Let me know which one you prefer!

