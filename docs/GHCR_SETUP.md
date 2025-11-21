# GitHub Container Registry (GHCR) Setup

## How It Works
The workflow automatically:
1. Uses `GITHUB_TOKEN` (automatically provided by GitHub Actions)
2. Logs in to `ghcr.io` using your GitHub username
3. Pushes images to: `ghcr.io/USERNAME/readmission-risk-api:latest`

##  Image Location
After the workflow runs,  images will be at:
ghcr.io/GITHUB-USERNAME/readmission-risk-api:latest
ghcr.io/GITHUB-USERNAME/readmission-risk-api:COMMIT-SHA

## Viewing Images
1. Go to your GitHub repository
2. Click **Packages** (on the right sidebar)
3. Or visit: `https://github.com/USERNAME?tab=packages`

## Pulling Images

To pull your image locally or on a server:

```bash
# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Pull image
docker pull ghcr.io/USERNAME/readmission-risk-api:latest
```

## For Public Repos

If the repo is **public**, images are automatically public and can be pulled without authentication.

## For Private Repos

If the repo is **private**, you need to:

1. **Make package public** (recommended for easier deployment):
   - Go to: Repository → Packages → readmission-risk-api
   - Package settings → Change visibility → Public

2. **Or use authentication** when pulling:
   ```bash
   # Create Personal Access Token with `read:packages` permission
   echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
   docker pull ghcr.io/USERNAME/readmission-risk-api:latest
   ```

## Permissions

The workflow includes:
```yaml
permissions:
  contents: read
  packages: write
```

This allows the workflow to:
- ✅ Read repository contents
- ✅ Write (push) packages to GHCR

Everything uses GitHub's built-in `GITHUB_TOKEN`!

## Deployment

When deploying to cloud platforms, use:

```
ghcr.io/USERNAME/readmission-risk-api:latest
```

**Example for Google Cloud Run:**
```bash
gcloud run deploy readmission-api \
  --image ghcr.io/USERNAME/readmission-risk-api:latest \
  --platform managed
```

## Summary
Just push to your repository and the workflow will automatically build and push to GHCR!

