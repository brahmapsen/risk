# Docker Hub Setup Guide

## GitHub Secrets Variable Names

For Docker Hub, use these **exact** variable names in GitHub Secrets:

### Required Secrets

1. **`DOCKER_REGISTRY`**
   - Value: `docker.io` (or leave empty - docker.io is the default)
   - This tells the workflow which registry to use

2. **`DOCKER_USERNAME`**
   - Value: Your Docker Hub username
   - Example: `myusername`

3. **`DOCKER_PASSWORD`**
   - ⚠️ **IMPORTANT**: This should be a **Docker Hub Access Token**, NOT your account password!
   - Docker Hub requires access tokens for API/CLI access
   - Your regular password won't work

## How to Get Docker Hub Access Token

### Step 1: Create Access Token

1. Go to [Docker Hub](https://hub.docker.com/)
2. Log in to your account
3. Click your username (top right) → **Account Settings**
4. Go to **Security** tab
5. Click **New Access Token**
6. Give it a name (e.g., "GitHub Actions")
7. Set permissions: **Read & Write** (or just **Write** if you only need to push)
8. Click **Generate**
9. **COPY THE TOKEN IMMEDIATELY** - you won't see it again!

### Step 2: Add to GitHub Secrets

1. Go to your GitHub repository
2. **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

Add these three secrets:

| Secret Name | Value | Example |
|------------|-------|---------|
| `DOCKER_REGISTRY` | `docker.io` | `docker.io` |
| `DOCKER_USERNAME` | Your Docker Hub username | `myusername` |
| `DOCKER_PASSWORD` | Your Docker Hub Access Token | `dckr_pat_xxxxx...` |

## Important Notes

### ❌ Don't Use Your Docker Hub Password
- Docker Hub passwords don't work for API/CLI authentication
- You **must** use an Access Token
- Access tokens are more secure (can be revoked individually)

### ✅ Use Access Token
- Access tokens start with `dckr_pat_`
- They can be scoped (read-only, write, etc.)
- Can be revoked if compromised
- Better security practice

## Testing Your Setup

After adding secrets, test locally:

```bash
# Login with your token
echo "YOUR_ACCESS_TOKEN" | docker login docker.io -u YOUR_USERNAME --password-stdin

# Build and push
docker build -t YOUR_USERNAME/readmission-risk-api:test .
docker push YOUR_USERNAME/readmission-risk-api:test
```

## Image Naming

With Docker Hub, your images will be:
- `YOUR_USERNAME/readmission-risk-api:latest`
- `YOUR_USERNAME/readmission-risk-api:COMMIT_SHA`

Example:
- If username is `johndoe`
- Image: `johndoe/readmission-risk-api:latest`

## Summary

**Variable Names** (exact spelling):
- ✅ `DOCKER_REGISTRY` = `docker.io`
- ✅ `DOCKER_USERNAME` = Your Docker Hub username
- ✅ `DOCKER_PASSWORD` = Docker Hub Access Token (NOT password!)

**Quick Checklist**:
- [ ] Created Docker Hub account
- [ ] Generated Access Token in Docker Hub
- [ ] Added `DOCKER_REGISTRY` secret = `docker.io`
- [ ] Added `DOCKER_USERNAME` secret = your username
- [ ] Added `DOCKER_PASSWORD` secret = access token (starts with `dckr_pat_`)

