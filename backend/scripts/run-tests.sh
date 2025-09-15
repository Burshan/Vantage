#!/bin/bash
# Test Runner Script
# Vantage Satellite System

set -e

echo "🧪 Running Vantage Satellite System Tests"
echo "========================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./scripts/dev-setup.sh first"
    exit 1
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Check if pytest is installed
if ! python -c "import pytest" &> /dev/null; then
    echo "📦 Installing pytest..."
    pip install pytest pytest-cov
fi

# Run architecture tests
echo "🏗️ Testing MVC architecture imports..."
python3 -c "
try:
    from app import create_app
    from controllers.user_controller import user_bp
    from controllers.aoi_controller import aoi_bp
    from services.satellite_service import SatelliteService
    from utils.decorators import require_auth
    print('✅ All MVC components import successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

# Run configuration tests
echo "🔧 Testing configuration..."
python3 -c "
try:
    from config import Config
    print(f'✅ Environment: {Config.ENVIRONMENT}')
    print(f'✅ Database URL configured: {\"Yes\" if Config.DATABASE_URL else \"No\"}')
    print(f'✅ Images directory: {Config.IMAGES_DIR}')
except Exception as e:
    print(f'❌ Configuration error: {e}')
    exit(1)
"

# Run database tests
echo "🗄️ Testing database connection..."
python3 -c "
try:
    from database import DatabaseManager
    from config import Config
    db_manager = DatabaseManager(Config.DATABASE_URL, Config.SQLALCHEMY_ENGINE_OPTIONS)
    with db_manager.get_session() as session:
        session.execute('SELECT 1')
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database error: {e}')
    exit(1)
"

# Run unit tests if they exist
if [ -d "tests" ] && [ "$(ls -A tests/*.py 2>/dev/null)" ]; then
    echo "🔬 Running unit tests..."
    python -m pytest tests/ -v --tb=short
else
    echo "ℹ️ No unit tests found in tests/ directory"
fi

# Test API endpoints (if server is running)
echo "🌐 Testing API endpoints..."
if curl -s http://localhost:5000/api/health > /dev/null; then
    echo "✅ API server is running"
    
    # Test health endpoint
    HEALTH_RESPONSE=$(curl -s http://localhost:5000/api/health)
    if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
        echo "✅ Health endpoint working"
    else
        echo "⚠️ Health endpoint response unexpected"
    fi
else
    echo "ℹ️ API server not running - skipping endpoint tests"
fi

echo ""
echo "🎉 Test run completed!"
echo ""
echo "📋 Test Summary:"
echo "  ✅ MVC Architecture imports"
echo "  ✅ Configuration loading"  
echo "  ✅ Database connectivity"
if [ -d "tests" ] && [ "$(ls -A tests/*.py 2>/dev/null)" ]; then
    echo "  ✅ Unit tests"
fi
if curl -s http://localhost:5000/api/health > /dev/null; then
    echo "  ✅ API endpoints"
fi