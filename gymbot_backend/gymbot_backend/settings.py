from pathlib import Path
from datetime import timedelta
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure--xz@5g&$g)nl!h+)cgde6q-c%!z5y@-_+&qd0mgnx5upoxdtj*'

DEBUG = True

ALLOWED_HOSTS = ['*']
# Uygulamalar
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',

    # Local apps
    'users',
    'workouts',

    # 3rd Party
    'rest_framework',
    'rest_framework.authtoken',
    'captcha',
]

# JWT + Session auth
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
}

# JWT Ayarları
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

# Custom user modeli
AUTH_USER_MODEL = 'users.CustomUser'

# Login yönlendirmeleri
LOGIN_URL = '/api/users/login/'
LOGIN_REDIRECT_URL = '/api/users/'  # Giriş sonrası yönlendirme

# Orta katmanlar
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    # Kullanıcı dilini aktif et
    'users.middleware.UserLanguageMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
]


ROOT_URLCONF = 'gymbot_backend.urls'

# Şablon ayarları
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'gymbot_backend.wsgi.application'

# Veritabanı
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Parola validasyonu
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

# Uluslararasılaştırma

LANGUAGE_CODE = 'en'  # varsayılan olarak İngilizce

LANGUAGES = [
    ('en', 'English'),
    ('tr', 'Turkish'),
]

LOCALE_PATHS = [os.path.join(BASE_DIR, 'locale')]
TIME_ZONE = 'Europe/Istanbul'
USE_TZ = True

# Statik dosyalar
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]

# Varsayılan model alanı tipi
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Gemini API anahtarı
GEMINI_API_KEY = "AIzaSyAi6lesWBaAaipT9_JyQYTbx57sq3DbgeE"


RECAPTCHA_PUBLIC_KEY = '
RECAPTCHA_PRIVATE_KEY = '6LdDHD8rAAAAAB5xKhrd_F8M4QUkURvk8xefV9SE'



EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'gymbot001@gmail.com'
EMAIL_HOST_PASSWORD = 'tofq evxo'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://localhost:3000',
    'http://localhost:*',  
    *[f"http://localhost:{port}" for port in range(50000, 60000)]     
]
