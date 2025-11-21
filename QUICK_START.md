# Quick Start Guide

## Option 1: Test Locally with Docker Compose

This builds the image locally and runs it for testing:

```bash
# 1. Make sure you have a trained model
python scripts/generate_data.py
python run.py

# 2. Build and run with docker-compose
docker-compose up --build

# This will:
# - Build the Docker image from Dockerfile
# - Start the API on http://localhost:8000
# - Start MLflow UI on http://localhost:5000
```

**Note**: `docker-compose up --build` will automatically build the image if it doesn't exist.

## Option 2: Let CI/CD Build and Push to GHCR

This is the **recommended** approach for deployment:

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Setup CI/CD with GHCR"
   git push origin main
   ```

2. **GitHub Actions will automatically**:
   - Build the Docker image
   - Push to GHCR: `ghcr.io/YOUR-USERNAME/readmission-risk-api:latest`
   - You can see it in: Repository → Actions → Your workflow run

3. **Then deploy from GHCR** to your cloud platform (Google Cloud Run, Railway, etc.)

## What's the Difference?

### Local Testing (docker-compose)
- ✅ Good for: Testing before pushing
- ✅ Builds image locally
- ✅ Runs on your machine
- ❌ Image stays on your machine

### CI/CD (GitHub Actions)
- ✅ Good for: Production deployment
- ✅ Builds image in GitHub
- ✅ Pushes to GHCR (accessible from anywhere)
- ✅ Automatic on every push
- ✅ Ready for cloud deployment

## Recommended Workflow

1. **Test locally first**:
   ```bash
   docker-compose up --build
   # Test at http://localhost:8000
   ```

2. **If it works, push to GitHub**:
   ```bash
   git push origin main
   ```

3. **CI/CD builds and pushes to GHCR automatically**

4. **Deploy from GHCR** to your cloud platform

## Next Steps After CI/CD Builds Image

Once your image is in GHCR, you can deploy to:

- **Google Cloud Run** (easiest)
- **Railway** (very simple)
- **AWS App Runner**
- **Any platform that supports Docker**

See `docs/DEPLOYMENT_OPTIONS.md` for details on each platform.

