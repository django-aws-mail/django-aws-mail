"""
Sandbox project settings.
"""
from pathlib import Path

DEBUG = True

SECRET_KEY = 'secret'

BASE_DIR = Path(__file__).resolve().parent.parent

ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = []


INSTALLED_APPS = [
    'sandbox',
    'django_aws_mail',

    # django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',

    # vendor
    'django_json_widget',
]


MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sandbox.urls'

WSGI_APPLICATION = 'sandbox.wsgi.application'


# HTTPS security settings
SECURE_SSL_REDIRECT = False
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# CSRF_COOKIE_SECURE = not DEBUG
# SESSION_COOKIE_SECURE = not DEBUG
# SECURE_CONTENT_TYPE_NOSNIFF = True
# SECURE_BROWSER_XSS_FILTER = True

# SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin-allow-popups'

X_FRAME_OPTIONS = 'DENY'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'OPTIONS': {
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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

AUTH_USER_MODEL = 'auth.User'

AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.AllowAllUsersModelBackend']


# Internationalization

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)

# STATIC_URL = '/static/'
# MEDIA_URL = '/media/'
#
# STATIC_ROOT = os.getenv('STATIC_LOCATION')
# MEDIA_ROOT = os.getenv('MEDIA_LOCATION')


# Logging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s [%(levelname)s] %(pathname)s (%(lineno)d): %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'django_aws_mail': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        }
    },
}


# Database

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        "NAME": "django_aws_mail.db",
    },
}


# Email

DEFAULT_FROM_EMAIL = '"Example" <noreply@example.com>'
SERVER_EMAIL = '"example" <noreply@example.com>'
ADMINS = ['"example" <admin@example.com>']

# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_BACKEND = 'django_aws_mail.backends.EmailBackend'
