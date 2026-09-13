"""
PostgreSQL test settings - uses actual PostgreSQL database for testing
including concurrency/locking behavior.
"""
from .settings import *

# Use PostgreSQL for testing (same as production settings)
# This allows proper testing of database locking and concurrency

# Override test database to use a separate test database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME') + '_test',  # Use separate test database
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'TEST': {
            'NAME': config('DB_NAME') + '_test',
        }
    }
}

# Add testserver to allowed hosts
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']
