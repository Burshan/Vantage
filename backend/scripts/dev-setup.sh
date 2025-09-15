#!/bin/bash
# Development Environment Setup Script
# Vantage Satellite System

set -e  # Exit on any error

echo "🚀 Setting up Vantage Satellite System Development Environment"
echo "============================================================"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "📚 Installing Python dependencies..."
    pip install -r requirements.txt
else
    echo "⚠️ requirements.txt not found. Installing basic dependencies..."
    pip install flask flask-cors sqlalchemy psycopg2-binary celery redis python-dotenv jwt pillow matplotlib numpy requests
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️ .env file not found. Please create one with the following variables:"
    echo "DATABASE_URL=your_database_url"
    echo "CLERK_SECRET_KEY=your_clerk_secret"
    echo "CLIENT_ID=your_sentinel_client_id" 
    echo "CLIENT_SECRET=your_sentinel_client_secret"
    echo "REDIS_URL=redis://localhost:6379/0"
else
    echo "✅ .env file found"
fi

# Check Redis
if command -v redis-server &> /dev/null; then
    echo "✅ Redis server found"
    if pgrep redis-server > /dev/null; then
        echo "✅ Redis is running"
    else
        echo "⚠️ Redis is installed but not running. Start it with: redis-server"
    fi
else
    echo "⚠️ Redis not found. Install with: brew install redis (macOS) or apt-get install redis (Ubuntu)"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p images logs

echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Configure your .env file with the required variables"
echo "2. Start Redis if not running: redis-server"
echo "3. Start Celery worker: ./scripts/start_celery.sh"
echo "4. Run the application: python app.py"
echo ""
echo "🔗 Useful commands:"
echo "   Development server: python app.py"
echo "   Run tests: python -m pytest tests/"
echo "   Start Celery: ./scripts/start_celery.sh"
echo "   Check health: curl http://localhost:5000/api/health"