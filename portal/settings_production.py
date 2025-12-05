# portal/settings.py (Critical Production Changes)

DEBUG = False
SECRET_KEY = 'YOUR_NEW_LONG_SECURE_KEY_HERE' # Generate a new, strong key
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com', 'your_vps_ip_address'] 

# Database Configuration (You will use PostgreSQL on the VPS)
# You will get the exact connection details from Ionos after setting up Postgres.
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'your_db_name',
#         'USER': 'your_db_user',
#         'PASSWORD': 'your_db_password',
#         'HOST': 'localhost', # Usually localhost if running on the same server
#     }
# }

# Configuration for Serving Files in Production
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'media'