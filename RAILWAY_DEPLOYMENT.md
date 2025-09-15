# Railway Deployment Guide

## 🚀 Quick Deploy Steps

### 1. Push to GitHub
```bash
git add .
git commit -m "Add Railway deployment config"
git push origin main
```

### 2. Deploy Backend Service

1. **Go to [Railway.app](https://railway.app) and sign up/login**
2. **Create new project** → "Deploy from GitHub repo"
3. **Select your repo** → Choose "vantage" repository
4. **Configure Backend Service:**
   - Service name: `vantage-backend`
   - Root directory: `backend`
   - Railway auto-detects Python

5. **Add Environment Variables** (Backend):
```bash
# Database - Railway will provide this automatically
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Environment
ENVIRONMENT=production
DEBUG=false

# API Configuration
API_HOST=0.0.0.0
API_PORT=$PORT
ALLOWED_ORIGINS=https://vantage-frontend-production.up.railway.app

# Authentication (Your Clerk keys)
CLERK_PUBLISHABLE_KEY=pk_live_your_publishable_key_here
CLERK_SECRET_KEY=sk_live_your_secret_key_here

# Satellite API (Your credentials)
CLIENT_ID=your_client_id_here
CLIENT_SECRET=your_client_secret_here

# AWS S3 (Your credentials)  
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_S3_REGION=us-east-1
AWS_S3_BUCKET=thevantage
S3_UPLOAD_ENABLED=true

# Image processing
USE_OPENCV=true
IMAGES_DIR=/app/images
```

### 3. Add Database

1. **In your Railway project** → Click "+" → "Database" → "PostgreSQL"
2. **Railway automatically provides** `DATABASE_URL` variable
3. **Backend will connect automatically**

### 4. Deploy Frontend Service

1. **In same Railway project** → Click "+" → "GitHub Repo"
2. **Select same repo** but different service:
   - Service name: `vantage-frontend`
   - Root directory: `frontend`

3. **Add Environment Variables** (Frontend):
```bash
# API endpoint (will be your backend's Railway URL)
REACT_APP_API_URL=https://vantage-backend-production.up.railway.app

# Environment
REACT_APP_ENVIRONMENT=production
```

### 5. Update CORS Settings

After both services deploy, **update backend CORS**:
1. Go to backend service settings
2. Update `ALLOWED_ORIGINS` with actual frontend URL:
```bash
ALLOWED_ORIGINS=https://your-frontend-url.up.railway.app
```

## 📋 Post-Deployment Checklist

### ✅ Test Backend
- Visit: `https://your-backend-url.up.railway.app/api/health`
- Should return: `{"status": "healthy"}`

### ✅ Test Frontend  
- Visit: `https://your-frontend-url.up.railway.app`
- Should load the login page

### ✅ Test Integration
- Try logging in through frontend
- Create an AOI
- Run analysis

### ✅ Verify Scheduler
- Check backend logs for:
```
🔄 בודק AOIs הזקוקים לניתוח אוטומטי...
```

## 🔗 Railway URLs

After deployment, you'll get:
- **Backend**: `https://vantage-backend-production.up.railway.app`
- **Frontend**: `https://vantage-frontend-production.up.railway.app`
- **Database**: Internal URL (auto-connected)

## 💰 Cost Tracking

- **Free tier**: $5/month usage credit
- **Monitor usage** in Railway dashboard
- **Typical usage**: $2-4/month for small apps

## 🛠 Troubleshooting

### Backend Issues
```bash
# Check logs in Railway dashboard
# Common issues:
# 1. Missing environment variables
# 2. Database connection (check DATABASE_URL)
# 3. S3 permissions
```

### Frontend Issues
```bash
# Check build logs
# Common issues:
# 1. Wrong REACT_APP_API_URL
# 2. CORS errors (update backend ALLOWED_ORIGINS)
```

### Scheduler Not Running
```bash
# Check backend logs for APScheduler startup
# Should see: "🤖 Automatic Analysis Scheduler: STARTED"
```

## 🔄 Updates

```bash
# Deploy updates:
git add .
git commit -m "Update message"
git push origin main

# Railway auto-deploys from GitHub!
```

Ready to deploy? Let's go! 🚀