"""
Django settings for the SEO Audit Tool.

Kept deliberately minimal per project requirements:
- No auth / user accounts
- No Celery / Redis / background workers
- SQLite only
- Single settings file (no base/dev/prod split)
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: change this before deploying anywhere public.
SECRET_KEY = "django-insecure-CHANGE-ME-before-deploying"

# SECURITY WARNING: don't run with DEBUG=True in production.
DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "audits",
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

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------------------
# SEO Audit Tool specific settings
# --------------------------------------------------------------------------

# Max time Playwright will wait for the initial "load" event.
SEO_AUDIT_NAVIGATION_TIMEOUT_MS = 20000

# Extra time Playwright will wait for network activity to settle after load.
# Not fatal if this times out (some pages poll forever) - we fall back to
# whatever was already captured at the "load" event.
SEO_AUDIT_NETWORK_IDLE_TIMEOUT_MS = 8000

# Cap on how many links get a broken-link HEAD/GET check, to keep the
# single audit request bounded in time.
SEO_AUDIT_MAX_LINKS_TO_CHECK = 20

# Timeout (seconds) for each individual broken-link check request.
SEO_AUDIT_LINK_CHECK_TIMEOUT_S = 4
