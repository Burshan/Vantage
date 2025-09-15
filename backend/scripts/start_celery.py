#!/usr/bin/env python3
"""
Celery Worker Startup Script
Run this to start the Celery worker process
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from celery_app import celery_app

if __name__ == '__main__':
    # Start Celery worker
    celery_app.start()