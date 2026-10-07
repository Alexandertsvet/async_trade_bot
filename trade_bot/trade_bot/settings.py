import os
from pathlib import Path

from data_keeper.clickhouse_module import ClickHouseProcessor
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR.parent / ".env" or BASE_DIR / ".env"
if not ENV_FILE.is_file():
    raise ImproperlyConfigured(
        f"Критическая ошибка: Файл конфигурации {ENV_FILE} отсутствует! "
        f"Создайте его на основе .env.example перед запуском проекта."
    )
SECRET_KEY = os.getenv("SECRET_KEY")
PASSWORD_MAIL = os.getenv("PASSWORD_MAIL")
USERNAME_MAIL = os.getenv("USERNAME_MAIL")
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
# --- PostgreSQL ---
PG_DB_NAME = os.getenv("PG_DB_NAME")
PG_USER = os.getenv("PG_USER")
PD_PASSWORD = os.getenv("PD_PASSWORD")
PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
# --- Clichouse ---
CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST")
CLICKHOUSE_PORT = os.getenv("CLICKHOUSE_PORT")
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD")
# --- DOCKER ---
IS_DOCKER = os.getenv("DOCKER_ENV", "False").lower() in ("true", "1", "t")

if not all([PG_DB_NAME, PG_USER, PD_PASSWORD, PG_HOST, PG_PORT]):
    raise ValueError(
        "Отсутствуют необходимые переменные окружения для PostgreSQL!"
    )
if not all(
    [CLICKHOUSE_HOST, CLICKHOUSE_PORT, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD]
):
    raise ValueError(
        "Отсутствуют необходимые переменные окружения для Clichouse!"
    )

FIELD_ENCRYPTION_KEY = os.getenv("FIELD_ENCRYPTION_KEY")
if not FIELD_ENCRYPTION_KEY:
    raise ValueError(
        "FIELD_ENCRYPTION_KEY отсутствует в переменной окружения!"
    )
FIELD_ENCRYPTION_KEY = FIELD_ENCRYPTION_KEY.encode("utf-8")
INVEST_TOKEN = os.getenv("INVEST_TOKEN")


ALLOWED_HOSTS = []


INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "user.apps.UserConfig",
    "homepage.apps.HomepageConfig",
    "data_recipient.apps.DataRecipientConfig",
    "data_keeper.apps.DataKeeperConfig",
    "terminal.apps.TerminalConfig",
    "channels",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "trade_bot.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

LOGIN_REDIRECT_URL = "homepage:homepage"
LOGOUT_REDIRECT_URL = "user:login"

WSGI_APPLICATION = "trade_bot.wsgi.application"
ASGI_APPLICATION = "trade_bot.asgi.application"


# Database
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": PG_DB_NAME,
        "USER": PG_USER,
        "PASSWORD": PD_PASSWORD,
        "HOST": PG_HOST,
        "PORT": PG_PORT,
    }
}
if not IS_DOCKER:
    DATABASES["default"]["HOST"] = "localhost"


# Password validation
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = "ru-ru"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.1/howto/static-files/


STATIC_URL = "static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]


# Email
# https://docs.djangoproject.com/en/6.1/topics/email/#topic-email-configuration
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "OPTIONS": {
            "host": "smtp.yandex.ru",
            "port": 465,
            "use_ssl": True,
            "username": USERNAME_MAIL,
            "password": PASSWORD_MAIL,
        },
    },
}
DEFAULT_FROM_EMAIL = USERNAME_MAIL
SERVER_EMAIL = USERNAME_MAIL

AUTH_USER_MODEL = "user.User"


if IS_DOCKER:
    # 1. Настройки для Docker-контейнеров
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
else:
    # 2. Локальная разработка без Docker (напрямую в хост-системе)
    REDIS_URL = "redis://127.0.0.1:6379/0"
    CELERY_BROKER_URL = "redis://127.0.0.1:6379/0"  # Используем явный IP вместо localhost для asyncio
    CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379/0"

print(
    f"//[SYSTEM_CHECK] ТЕКУЩИЙ АДРЕС REDIS: {REDIS_URL} (IS_DOCKER={IS_DOCKER})"
)

# Конфигурация Django Channels (ИСПРАВЛЕНО)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [
                {
                    "address": REDIS_URL,
                    "socket_connect_timeout": 5,
                    "socket_timeout": 30,
                    "health_check_interval": 5,
                    "retry_on_timeout": True,
                }
            ],
            "capacity": 5000,
            "expiry": 10,
        },
    },
}

# Общие настройки Celery
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Europe/Moscow"
CELERY_BEAT_SCHEDULE = {
    "flush_redis_to_clickhouse_job": {
        "task": "data_recipient.tasks.flush_redis_to_clickhouse",
        "schedule": 10.0,
    },
}

client_clickhouse = ClickHouseProcessor()
print(
    f"//CLICHOUSE_DRIVER VERSION//{client_clickhouse.execute('SELECT version();')}"
)


LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": (
                "[%(asctime)s] %(levelname)-8s [%(name)s:%(filename)s:%(lineno)d] "
                "[Process:%(process)d Thread:%(thread)d] %(message)s"
            ),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "[%(asctime)s] %(levelname)-8s [%(module)s] %(message)s",
            "datefmt": "%H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file_general": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/django_general.log",
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 5,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
        "file_errors": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/django_errors.log",
            "maxBytes": 1024 * 1024 * 10,
            "backupCount": 10,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console", "file_general", "file_errors"],
            "level": "INFO",
        },
        "django": {
            "handlers": ["console", "file_general", "file_errors"],
            "level": "INFO",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": [],  # "console"
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
