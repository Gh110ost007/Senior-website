import os
from pathlib import Path

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin123'
    ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN') or 'changeme-admin-token'
    SITE_URL = os.environ.get('SITE_URL') or 'http://127.0.0.1:5000'
    
    # Database
    BASE_DIR = Path(__file__).resolve().parent
    INSTANCE_DIR = BASE_DIR / "instance"
    INSTANCE_DIR.mkdir(exist_ok=True)
    DB_PATH = INSTANCE_DIR / "analytics.db"

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    FLASK_ENV = 'production'
    
    # Override with environment variables in production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN')
    SITE_URL = os.environ.get('SITE_URL')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
