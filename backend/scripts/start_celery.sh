#!/bin/bash
# Start Celery Worker and Beat (scheduler)

# Make sure we're in the right directory
cd "$(dirname "$0")"

echo "🚀 Starting Redis..."
redis-server --daemonize yes

echo "🚀 Starting Celery Worker..."
python3 -m celery -A celery_app.celery_app worker --loglevel=info --detach

echo "🚀 Starting Celery Beat (Scheduler)..."
python3 -m celery -A celery_app.celery_app beat --loglevel=info --detach

echo "✅ Celery services started!"
echo "📊 Check worker status: celery -A celery_app.celery_app status"
echo "🛑 Stop services: pkill -f celery"