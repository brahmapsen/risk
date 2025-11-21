# Docker Registry Guide

The `DOCKER_REGISTRY` value depends on which container registry you're using.

## Common Registry Options

### 1. Docker Hub (docker.io)
**Value**: `docker.io` (or leave empty - it's the default)

**Usage**:
```yaml
DOCKER_REGISTRY: docker.io
# Or just use: your-username/readmission-risk-api
```

**Example tags**:
- `docker.io/yourusername/readmission-risk-api:latest`
- `yourusername/readmission-risk-api:latest` (docker.io is implied)

**Authentication**:
- Username: Your Docker Hub username
- Password: Docker Hub access token (not your password!)

### 2. GitHub Container Registry (GHCR) - Recommended for GitHub repos
**Value**: `ghcr.io`

**Usage**:
```yaml
DOCKER_REGISTRY: ghcr.io
```

**Example tags**:
- `ghcr.io/your-org/readmission-risk-api:latest`
- `ghcr.io/your-username/readmission-risk-api:latest`

**Authentication**:
- Username: Your GitHub username
- Password: GitHub Personal Access Token (PAT) with `write:packages` permission

**Benefits**:
- Free for public repos
- Integrated with GitHub
- No separate account needed

### 3. AWS Elastic Container Registry (ECR)
**Value**: `<account-id>.dkr.ecr.<region>.amazonaws.com`

**Usage**:
```yaml
DOCKER_REGISTRY: 123456789012.dkr.ecr.us-east-1.amazonaws.com
```

**Example tags**:
- `123456789012.dkr.ecr.us-east-1.amazonaws.com/readmission-risk-api:latest`

**Authentication**:
- Username: `AWS`
- Password: Use AWS CLI to get temporary token:
  ```bash
  aws ecr get-login-password --region us-east-1
  ```

### 4. Google Container Registry (GCR)
**Value**: `gcr.io`

**Usage**:
```yaml
DOCKER_REGISTRY: gcr.io
```

**Example tags**:
- `gcr.io/your-project-id/readmission-risk-api:latest`

**Authentication**:
- Username: `oauth2accesstoken`
- Password: Use `gcloud auth print-access-token`

### 5. Azure Container Registry (ACR)
**Value**: `<registry-name>.azurecr.io`

**Usage**:
```yaml
DOCKER_REGISTRY: myregistry.azurecr.io
```

**Example tags**:
- `myregistry.azurecr.io/readmission-risk-api:latest`

**Authentication**:
- Username: Registry name
- Password: Admin password or service principal

## Recommended Setup

### For GitHub Projects: Use GHCR

1. **Enable GitHub Packages** (already enabled if you have a GitHub repo)

2. **Create Personal Access Token**:
   - Go to: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Generate new token with `write:packages` permission
   - Save this as `DOCKER_PASSWORD` secret

3. **Set GitHub Secrets**:
   ```
   DOCKER_REGISTRY: ghcr.io
   DOCKER_USERNAME: your-github-username
   DOCKER_PASSWORD: your-personal-access-token
   ```

4. **Image will be at**:
   ```
   ghcr.io/your-username/readmission-risk-api:latest
   ```

### For Docker Hub

1. **Create Docker Hub account** (if you don't have one)

2. **Create Access Token**:
   - Go to: Docker Hub → Account Settings → Security → New Access Token
   - Save this as `DOCKER_PASSWORD` secret (NOT your password!)

3. **Set GitHub Secrets**:
   ```
   DOCKER_REGISTRY: docker.io
   DOCKER_USERNAME: your-dockerhub-username
   DOCKER_PASSWORD: your-access-token
   ```

## Quick Decision Guide

- **Using GitHub?** → Use `ghcr.io` (easiest, free for public repos)
- **Using AWS?** → Use ECR (integrated with AWS services)
- **Using GCP?** → Use GCR or Artifact Registry
- **Using Azure?** → Use ACR
- **Just want simple?** → Use Docker Hub (`docker.io`)

## Testing Your Registry

After setting up, test with:

```bash
# Login
docker login $DOCKER_REGISTRY -u $DOCKER_USERNAME -p $DOCKER_PASSWORD

# Build and push
docker build -t $DOCKER_REGISTRY/readmission-risk-api:test .
docker push $DOCKER_REGISTRY/readmission-risk-api:test
```

