from celery import Celery
from config import Config
import os

def make_celery(app_name=__name__):
    """Create Celery instance"""
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    celery = Celery(
        app_name,
        broker=redis_url,
        backend=redis_url,
        include=['tasks']  # Include our task modules
    )
    
    # Configure Celery
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        beat_schedule={},  # We'll populate this dynamically
        beat_schedule_filename='celerybeat-schedule',
    )
    
    return celery

# Create Celery app
celery_app = make_celery('vantage_satellite')