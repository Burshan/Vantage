import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Environment
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL')
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///satellite_monitor.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Authentication - Clerk
    CLERK_PUBLISHABLE_KEY = os.getenv('CLERK_PUBLISHABLE_KEY')
    CLERK_SECRET_KEY = os.getenv('CLERK_SECRET_KEY')
    
    # Satellite API
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    
    # File Storage
    IMAGES_DIR = os.getenv('IMAGES_DIR', 'images')
   # SQLAlchemy Configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_timeout': 30,
        'pool_recycle': 1800,  # Recycle connections every 30 minutes instead of 60
        'max_overflow': 20,
        'pool_pre_ping': True,  # Test connections before using them
        'connect_args': {
            'connect_timeout': 10,
            'keepalives_idle': 30,
            'keepalives_interval': 5,
            'keepalives_count': 5,
        },
        'echo': os.getenv('DEBUG', 'false').lower() == 'true'
    }

    
    # Image processing configuration
    USE_OPENCV = os.getenv('USE_OPENCV', 'true').lower() == 'true'
    
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY') 
    AWS_S3_REGION = os.getenv('AWS_S3_REGION', 'us-east-1')
    AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET')
    S3_UPLOAD_ENABLED = os.getenv('S3_UPLOAD_ENABLED', 'true').lower() == 'true'
    
    # API Configuration
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', '5000'))
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')