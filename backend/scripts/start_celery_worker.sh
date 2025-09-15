#!/bin/bash
cd /Users/omer.burshan1gmail.com/vantage/backend

echo "🚀 Starting Celery worker for Vantage Satellite System..."
echo "📋 Available tasks:"
python3 -c "from celery_app import celery_app; print('\n'.join([t for t in celery_app.tasks.keys() if 'tasks.' in t]))"

echo ""
echo "🔄 Starting worker with INFO logging..."

# Start Celery worker with appropriate settings
celery -A celery_app worker \
  --loglevel=info \
  --concurrency=2 \
  --queues=celery \
  --hostname=vantage-worker@%h