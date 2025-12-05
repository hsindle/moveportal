"""
Django settings for portal project.
"""

from pathlib import Path
import os
# Required for PostgreSQL connection URL parsing
import dj_database_url 

SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- FILE SERVING PATHS ---
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Nginx serves from here

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'        # User uploaded files (Right to Work proof, etc.)


# --- CORE SECURITY & DEBUGGING ---
# SECURITY WARNING: DON'T run with debug turned on in production!
DEBUG = False 
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-wb!79r+-uss=lo)jfuei)3us7f&jj_*^-%r#yvw64w@_x358ui')
ALLOWED_HOSTS = ['moveandbomba.com', 'www.moveandbomba.com', '87.106.203.42', 'localhost']


AUTH_USER_MODEL = 'accounts.CustomUser'


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_bootstrap4',

    'crispy_forms',  # for nice forms

    # Your apps
    'accounts',
    'checklists',
    'rota',
    'events',
    'training',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'portal.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug', 
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'portal.wsgi.application'


# --- DATABASE CONFIGURATION ---

# In production, this should be PostgreSQL. 
# You should update this to your PostgreSQL credentials on the VPS.
# EXAMPLE POSTGRES CONFIGURATION (Replace placeholders):
#DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'nightclub_db', # Name you created
#         'USER': 'nightclub_user', # User you created
#        'PASSWORD': 'Bluecat3033!', 
#         'HOST': 'localhost',
#         'PORT': '5432',
     }
 }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --- AUTHENTICATION AND SECURITY ---
LOGIN_URL = '/accounts/login/' 
# 🚨 FIX: Redirect to the bare root path (/) 🚨
LOGIN_REDIRECT_URL = '/' 
LOGOUT_REDIRECT_URL = '/accounts/login/'

# 🚨 CRITICAL SSL/HTTPS FIX 🚨
# These settings resolve the ERR_TOO_MANY_REDIRECTS loop when Nginx handles SSL.
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_TRUSTED_ORIGINS = ['https://yourdomain.com', 'https://www.yourdomain.com'] # Add HTTPS domains

# Ensure session cookies are secure
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True


# CRISPY FORMS SETTINGS
CRISPY_ALLOWED_TEMPLATE_PACKS = ('bootstrap4', 'bootstrap5',) 
CRISPY_TEMPLATE_PACK = 'bootstrap4'
