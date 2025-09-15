# Vantage Platform - Deployment Guide

## Architecture Overview

The Vantage platform consists of two independent applications:
- **Backend**: Flask API server (Python)
- **Frontend**: React.js application (Node.js)

Both applications are fully decoupled and communicate via REST API calls.

## Prerequisites

- Docker & Docker Compose
- Domain name (for production)
- AWS S3 bucket (for image storage)
- Clerk account (for authentication)
- Satellite API credentials

## Environment Configuration

### 1. Backend Environment Variables

Copy `backend/.env.example` to `backend/.env` and configure:

```bash
# Required - Database
DATABASE_URL=postgresql://user:password@host:port/database

# Required - Authentication
CLERK_PUBLISHABLE_KEY=pk_live_your_key
CLERK_SECRET_KEY=sk_live_your_secret

# Required - Satellite API
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret

# Required - AWS S3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET=your-bucket-name

# Optional - API Configuration
API_HOST=0.0.0.0
API_PORT=5000
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 2. Frontend Environment Variables

Copy `frontend/.env.example` to `frontend/.env` and configure:

```bash
# Required - API endpoint
REACT_APP_API_URL=https://api.yourdomain.com

# Optional
REACT_APP_ENVIRONMENT=production
```

### 3. Docker Compose Environment

Create `.env` in the root directory for Docker Compose:

```bash
# Authentication
CLERK_PUBLISHABLE_KEY=pk_live_your_key
CLERK_SECRET_KEY=sk_live_your_secret

# Satellite API
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret

# AWS S3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET=your-bucket-name
AWS_S3_REGION=us-east-1
S3_UPLOAD_ENABLED=true
```

## Deployment Options

### Option 1: Docker Compose (Recommended for Development/Testing)

```bash
# Clone the repository
git clone <your-repo-url>
cd vantage

# Configure environment variables (see above)
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
cp .env.example .env

# Edit the .env files with your configuration

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Access the application
# Frontend: http://localhost
# Backend API: http://localhost:5000
```

### Option 2: Separate Deployment (Production)

#### Backend Deployment

```bash
cd backend

# Build Docker image
docker build -t vantage-backend .

# Run with environment variables
docker run -d \
  --name vantage-backend \
  -p 5000:5000 \
  --env-file .env \
  vantage-backend
```

#### Frontend Deployment

```bash
cd frontend

# Set build-time environment variables
export REACT_APP_API_URL=https://your-api-domain.com

# Build Docker image
docker build -t vantage-frontend .

# Run
docker run -d \
  --name vantage-frontend \
  -p 80:80 \
  vantage-frontend
```

### Option 3: Cloud Platforms

#### AWS ECS/Fargate
- Use the provided Dockerfiles
- Configure environment variables in ECS task definitions
- Set up Application Load Balancer for HTTPS

#### Google Cloud Run
- Deploy each container separately
- Configure environment variables in Cloud Run service settings
- Use Cloud SQL for PostgreSQL

#### Azure Container Instances
- Deploy using the Docker images
- Configure environment variables in container settings
- Use Azure Database for PostgreSQL

## Production Checklist

### Security
- [ ] Use HTTPS for all communications
- [ ] Set secure CORS origins in `ALLOWED_ORIGINS`
- [ ] Use production Clerk keys
- [ ] Rotate AWS credentials regularly
- [ ] Enable database SSL connections

### Performance
- [ ] Configure CDN for frontend assets
- [ ] Set up database connection pooling
- [ ] Enable S3 lifecycle policies for image cleanup
- [ ] Configure nginx gzip compression (already included)

### Monitoring
- [ ] Set up health check endpoints (already included)
- [ ] Configure logging aggregation
- [ ] Set up error tracking (Sentry recommended)
- [ ] Monitor database performance

### Backup
- [ ] Set up automated database backups
- [ ] Configure S3 bucket versioning
- [ ] Test restoration procedures

## Scaling Considerations

### Horizontal Scaling
- Backend: Stateless, can run multiple instances behind load balancer
- Frontend: Static files, use CDN for global distribution
- Database: Use read replicas for read-heavy workloads

### Database Optimization
- Add indexes for frequently queried fields
- Consider partitioning for large analysis_history table
- Monitor slow queries

## Troubleshooting

### Common Issues

1. **CORS Errors**
   - Check `ALLOWED_ORIGINS` includes your frontend domain
   - Ensure protocol (http/https) matches

2. **Database Connection Issues**
   - Verify DATABASE_URL format
   - Check network connectivity and firewall rules
   - Ensure database accepts SSL connections

3. **S3 Upload Failures**
   - Verify AWS credentials and permissions
   - Check bucket policy and CORS configuration
   - Ensure bucket exists in correct region

4. **Authentication Issues**
   - Verify Clerk keys are for correct environment
   - Check JWT token validation

### Health Checks

```bash
# Backend health
curl http://your-backend-domain/api/health

# Frontend health  
curl http://your-frontend-domain/health

# Database connection
# Check backend logs for database connectivity
```

## Development vs Production

| Component | Development | Production |
|-----------|-------------|------------|
| Database | Local PostgreSQL/SQLite | Managed PostgreSQL |
| Frontend | localhost:3000 | Custom domain |
| Backend | localhost:5000 | Custom domain |
| HTTPS | Not required | Required |
| CORS | Permissive | Restrictive |
| Auth | Test keys | Production keys |

## Maintenance

### Regular Tasks
- Monitor disk usage (database, S3, logs)
- Review and rotate API keys
- Update dependencies
- Monitor error rates and performance metrics

### Updates
- Test in staging environment first
- Use blue-green deployment for zero downtime
- Backup database before major updates