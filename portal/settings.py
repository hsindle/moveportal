"""
Django settings for portal project.
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# Quick-start development settings - unsuitable for production
SECRET_KEY = 'django-insecure-wb!79r+-uss=lo)jfuei)3us7f&jj_*^-%r#yvw64w@_x358ui'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# 🚨 FIX 1: Set ALLOWED_HOSTS for local development (Cleared CommandError)
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    '192.168.1.44'  # Your PC's IP
]

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


# Middleware (add your ForcePasswordChangeMiddleware AFTER AuthenticationMiddleware)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    #'accounts.middleware.ForcePasswordChangeMiddleware',  # <- add here
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
                # 🚨 FIX 3: Added debug processor (Cleared admin.E403)
                'django.template.context_processors.debug',    
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'portal.wsgi.application'


# Database
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


# Authentication
LOGIN_URL = '/accounts/login/' 
# 🚨 FIX: Change redirect target from '/checklists/' to '/' 🚨
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# 🚨 FIX: CRISPY FORMS SETTINGS 🚨
# Tell crispy forms which template pack to use.

CRISPY_ALLOWED_TEMPLATE_PACKS = ('bootstrap4', 'bootstrap5',) 
CRISPY_TEMPLATE_PACK = 'bootstrap4'
