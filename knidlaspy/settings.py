"""
Django settings for knidlaspy project.
SMART VERSION: Auto-detects Local vs Render
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- 1. DETECT ENVIRONMENT ---
# Render always sets a 'RENDER' environment variable.
# If this is missing, we know we are on your Local Computer.
ON_RENDER = 'RENDER' in os.environ

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-local-dev-key')

# SECURITY WARNING: don't run with debug turned on in production!
# Local: True | Render: False (unless you set it otherwise)
DEBUG = not ON_RENDER

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # WhiteNoise is ONLY added below if we are on Render
]

ROOT_URLCONF = 'knidlaspy.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# NOTE: This is required for runserver too, don't remove it!
WSGI_APPLICATION = 'knidlaspy.wsgi.application'


# --- 2. SMART DATABASE SWITCHER ---

if ON_RENDER:
    # === PRODUCTION SETTINGS (RENDER) ===
    import dj_database_url
    
    # Add WhiteNoise Middleware only here
    MIDDLEWARE.append('whitenoise.middleware.WhiteNoiseMiddleware')
    
    # Use Neon DB
    DATABASES = {
        'default': dj_database_url.config(
            default='sqlite:///db.sqlite3',
            conn_max_age=600
        )
    }
else:
    # === LOCAL SETTINGS (YOUR COMPUTER) ===
    # No fancy imports. Just simple SQLite.
    print("🖥️  Running Locally: Using db.sqlite3")
    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# Only set the root if on Render to avoid path errors
if ON_RENDER:
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    # Enable WhiteNoise compression
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

LOGIN_REDIRECT_URL = 'game'
LOGOUT_REDIRECT_URL = 'login'