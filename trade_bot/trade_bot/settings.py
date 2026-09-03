from dotenv import load_dotenv
from pathlib import Path
import os
load_dotenv()



BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG")


ALLOWED_HOSTS = []


INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'user.apps.UserConfig',
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

ROOT_URLCONF = 'trade_bot.urls'

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

WSGI_APPLICATION = 'trade_bot.wsgi.application'
ASGI_APPLICATION = 'trade_bot.asgi.application'


# Database
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = "ru-ru"

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.1/howto/static-files/

STATIC_URL = 'static/'


# Email
# https://docs.djangoproject.com/en/6.1/topics/email/#topic-email-configuration

MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}

AUTH_USER_MODEL = 'user.User'


"""
#1
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    },

    'clickhouse': {
        'ENGINE': 'clickhouse_backend.backend',
        'NAME': os.environ.get('CH_NAME', 'default'),
        'USER': os.environ.get('CH_USER', 'default'),
        'PASSWORD': os.environ.get('CH_PASSWORD', ''),
        'HOST': os.environ.get('CH_HOST', '127.0.0.1'),
        'PORT': os.environ.get('CH_PORT', '9000'), 
        'OPTIONS': {
            'settings': {
                'async_insert': 1,            
                'wait_for_async_insert': 0, 
            }
        }
    }
}
#2
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_pg_db',
        'USER': 'your_pg_user',
        'PASSWORD': 'your_pg_password',
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'async_client': True, 
        },
    }
}

CLICKHOUSE_DATABASES = {
    'default': {
        'ENGINE': 'django_clickhouse_backend',
        'NAME': 'your_ch_db',
        'USER': 'default',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '9000', # Родной TCP порт ClickHouse
    }
}

DATABASE_ROUTERS = ['django_clickhouse_backend.routers.ClickHouseRouter']
"""