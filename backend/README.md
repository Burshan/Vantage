# 🛰️ Vantage Satellite Intelligence System

> **Professional MVC Architecture** | **Real-time Satellite Analysis** | **Change Detection** | **Scheduled Monitoring**

A sophisticated satellite intelligence platform that provides real-time analysis of geographic areas using Sentinel-2 satellite imagery, with automated change detection, baseline comparisons, and scheduled monitoring capabilities.

## 🚀 Features

### 🎯 **Core Capabilities**
- **🗺️ Area of Interest (AOI) Management** - Define and manage geographic regions for monitoring
- **📸 Satellite Image Analysis** - Download and process Sentinel-2 satellite imagery
- **🔥 Change Detection** - Advanced heatmap generation for identifying changes over time
- **⏰ Scheduled Monitoring** - Automated periodic analysis with Celery task queue
- **📊 Baseline Comparisons** - Compare current images against historical baselines
- **🔐 Secure Authentication** - Clerk-based JWT authentication system
- **💳 Token Management** - Usage-based token system for API rate limiting

### 🏗️ **Architecture Highlights**
- **Professional MVC Structure** - Controllers, Services, and Utilities properly separated
- **Blueprint-based Routing** - Modular and maintainable API endpoints
- **Service Layer Pattern** - Reusable business logic components
- **Standardized Responses** - Consistent JSON API responses with proper HTTP status codes
- **Centralized Error Handling** - Comprehensive error management across the application
- **Asynchronous Processing** - Background tasks with Celery and Redis

## 📁 Project Structure

```
backend/
├── 📄 app.py                    # Main application entry point (87 lines)
├── 📄 ARCHITECTURE.md           # Detailed architecture documentation
├── 📄 README.md                 # This file
│
├── 🎮 controllers/              # HTTP Request Handlers
│   ├── admin_controller.py      # Health, stats, debug, images
│   ├── aoi_controller.py        # AOI CRUD operations  
│   ├── analysis_controller.py   # Manual analysis execution
│   ├── baseline_controller.py   # Baseline image management
│   ├── schedule_controller.py   # Scheduling & monitoring
│   └── user_controller.py       # User profile & history
│
├── 🔧 services/                 # Business Logic Layer
│   ├── satellite_service.py     # Sentinel Hub API integration
│   └── baseline_service.py      # Baseline image creation
│
├── 🛠️ utils/                    # Cross-cutting Utilities
│   ├── decorators.py            # Auth & error handling decorators
│   └── responses.py             # Standardized API responses
│
├── 🔒 middleware/               # Application Middleware
│   └── error_handlers.py        # Centralized error handling
│
├── 📚 scripts/                  # Development & Deployment
│   ├── dev-setup.sh            # Development environment setup
│   ├── run-tests.sh            # Test runner
│   └── start_celery.sh         # Celery worker starter
│
├── 🧪 tests/                   # Test Files
├── 📦 archive/                 # Legacy code backup
└── 🖼️ images/                  # Generated satellite images
```

## 🚀 Quick Start

### 1. **Setup Development Environment**
```bash
# Clone and setup
git clone <your-repo>
cd backend/

# Run automated setup
./scripts/dev-setup.sh
```

### 2. **Configure Environment**
Create a `.env` file with your credentials:
```bash
DATABASE_URL=postgresql://user:password@host:port/database
CLERK_SECRET_KEY=your_clerk_secret_key
CLIENT_ID=your_sentinel_hub_client_id
CLIENT_SECRET=your_sentinel_hub_client_secret
REDIS_URL=redis://localhost:6379/0
```

### 3. **Start Services**
```bash
# Start Redis (in separate terminal)
redis-server

# Start Celery worker (in separate terminal)  
./scripts/start_celery.sh

# Start the application
python app.py
```

### 4. **Verify Installation**
```bash
# Run tests
./scripts/run-tests.sh

# Check health
curl http://localhost:5000/api/health
```

## 📋 API Endpoints

### 🔐 **Authentication**
All endpoints require Clerk JWT authentication via `Authorization: Bearer <token>` header.

### 👤 **User Management**
```http
GET  /api/user/profile     # Get user profile & token balance
GET  /api/user/history     # Get analysis history
```

### 🗺️ **Area of Interest (AOI)**
```http
GET    /api/aoi                    # List user's AOIs
POST   /api/aoi                    # Create new AOI
GET    /api/aoi/{id}               # Get AOI dashboard
DELETE /api/aoi/{id}               # Delete AOI
GET    /api/aoi/{id}/history       # Get AOI analysis history
GET    /api/aoi/{id}/dashboard     # Detailed dashboard view
```

### 🔬 **Analysis**
```http
POST /api/process-satellite-images     # Manual image analysis
POST /api/aoi/{id}/run-analysis        # Run AOI analysis
```

### ⏰ **Scheduling**  
```http
GET    /api/aoi/{id}/schedule-monitoring    # Get schedule info
POST   /api/aoi/{id}/schedule-monitoring    # Create/update schedule
DELETE /api/aoi/{id}/schedule-monitoring    # Remove schedule
GET    /api/scheduler/status                # Scheduler status
POST   /api/scheduler/trigger/{id}          # Manual trigger
```

### 🖼️ **Baseline Management**
```http
POST /api/aoi/{id}/baseline    # Create baseline image
GET  /api/aoi/{id}/baseline    # Get baseline status
```

### 🔧 **System**
```http
GET /api/health              # Health check
GET /api/admin/stats         # System statistics
GET /api/debug/ping          # Simple ping
GET /api/image/{filename}    # Serve images
```

## 🧪 Testing

```bash
# Run all tests
./scripts/run-tests.sh

# Run specific test file
python -m pytest tests/test_specific.py

# Test with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

## 📊 Monitoring

### **Health Checks**
```bash
curl http://localhost:5000/api/health
```

### **Celery Monitoring**
```bash
# Check worker status
celery -A celery_app inspect active

# Monitor tasks
celery -A celery_app events
```

### **Database**
```bash
# Connect to database
psql $DATABASE_URL
```

## 🔧 Development

### **Adding New Endpoints**
1. Create controller method in appropriate controller
2. Add route with `@blueprint.route()`  
3. Add authentication with `@require_auth`
4. Add error handling with `@handle_errors`
5. Return standardized response using `utils.responses`

### **Adding Business Logic**
1. Create service class in `services/`
2. Implement business logic methods
3. Import and use in controllers
4. Write unit tests

### **Database Changes**
1. Update models in `models.py`
2. Create migration script
3. Test migration on development database
4. Update API endpoints as needed

## 🚀 Production Deployment

### **Environment Setup**
```bash
# Production environment variables
export ENVIRONMENT=production
export DEBUG=False
export DATABASE_URL=<production_db_url>
export REDIS_URL=<production_redis_url>
```

### **Docker Deployment**
```dockerfile
# Dockerfile example
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

### **Scaling Considerations**
- **Multiple Workers**: Scale Celery workers horizontally
- **Load Balancing**: Use nginx or cloud load balancer  
- **Database**: Use connection pooling and read replicas
- **Redis**: Implement Redis clustering for high availability
- **Images**: Store images in cloud storage (S3, GCS)

## 📚 Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed architecture overview
- **API Documentation** - Available at `/api/docs` (when enabled)
- **Code Documentation** - Inline docstrings throughout codebase

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Issues**: GitHub Issues
- **Documentation**: See `docs/` directory
- **Architecture**: See `ARCHITECTURE.md`

---

🛰️ **Built with precision for satellite intelligence** | **MVC Architecture** | **Production Ready**
