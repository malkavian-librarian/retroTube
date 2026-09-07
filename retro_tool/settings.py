"""
Django settings for retro_tool project.

See _docs/arch.md for the stack rationale behind these choices.
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(env_file)

# SECURITY WARNING: keep the secret key used in production secret!
# No insecure fallback in production — fail fast if unset while DEBUG=False.
DEBUG = env("DEBUG")
SECRET_KEY = env(
    "SECRET_KEY",
    default=(
        "django-insecure-local-dev-only-do-not-use-in-production" if DEBUG else environ.Env.NOTSET
    ),
)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"] if DEBUG else [])


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",
    "retros",
    "boards",
    "voting",
    "actions",
    "realtime",
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

ROOT_URLCONF = "retro_tool.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "retro_tool.wsgi.application"
ASGI_APPLICATION = "retro_tool.asgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
#
# Production (Railway) sets DATABASE_URL to a Postgres connection string.
# Local dev without DATABASE_URL falls back to a SQLite file for a
# zero-setup `manage.py test` / `pytest` run — see .env.example.
DATABASE_URL = env("DATABASE_URL", default="")
DATABASES = {
    "default": (
        env.db_url_config(DATABASE_URL)
        if DATABASE_URL
        else env.db_url_config(f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
    ),
}

# Redis — Channels layer backend (see _docs/arch.md). Local dev without
# REDIS_URL falls back to the in-memory layer, which is fine for scaffolding
# since no consumers are wired up yet.
REDIS_URL = env("REDIS_URL", default="")
if REDIS_URL:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [REDIS_URL]},
        },
    }
else:
    CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
    }


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
