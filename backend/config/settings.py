"""
Django settings for the Local RAG backend.

Deployment-level configuration comes from environment variables (or a .env file
at the repository root). Everything tunable at runtime by the user lives in the
database (AppSettings) and is managed through the API.
"""

from pathlib import Path

import environ

# backend/
BASE_DIR = Path(__file__).resolve().parent.parent
# repository root
ROOT_DIR = BASE_DIR.parent

env = environ.Env(
    DEBUG=(bool, True),
    ALLOWED_HOSTS=(list, ["127.0.0.1", "localhost"]),
    CORS_ALLOWED_ORIGINS=(
        list,
        ["http://localhost:5173", "http://127.0.0.1:5173"],
    ),
    DATA_DIR=(str, str(ROOT_DIR / "data")),
    OLLAMA_BASE_URL=(str, "http://localhost:11434"),
    OLLAMA_CONNECT_TIMEOUT=(float, 5.0),
    OLLAMA_REQUEST_TIMEOUT=(float, 600.0),
)
environ.Env.read_env(ROOT_DIR / ".env")

SECRET_KEY = env(
    "SECRET_KEY",
    default="django-insecure-local-development-only-change-me",
)
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "corsheaders",
    "rest_framework",
    "drf_spectacular",
    # Local apps
    "kb",
    "chat",
    "llm",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
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
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

DATA_DIR = Path(env("DATA_DIR"))
if not DATA_DIR.is_absolute():
    # Resolve relative paths against the repository root, not the process cwd,
    # so manage.py behaves the same from backend/ or the repo root.
    DATA_DIR = ROOT_DIR / DATA_DIR
DATA_DIR = DATA_DIR.resolve()

MEDIA_ROOT = DATA_DIR / "media"
CHROMA_DIR = DATA_DIR / "chroma"
STATIC_ROOT = DATA_DIR / "static"

DATA_DIR.mkdir(parents=True, exist_ok=True)
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATA_DIR / "db.sqlite3",
        "OPTIONS": {
            # The ingestion worker and request handlers share this database.
            "timeout": 20,
        },
    }
}

MEDIA_URL = "/media/"
STATIC_URL = "static/"

# ---------------------------------------------------------------------------
# Local models
# ---------------------------------------------------------------------------

OLLAMA_BASE_URL = env("OLLAMA_BASE_URL").rstrip("/")
OLLAMA_CONNECT_TIMEOUT = env("OLLAMA_CONNECT_TIMEOUT")
OLLAMA_REQUEST_TIMEOUT = env("OLLAMA_REQUEST_TIMEOUT")

# Ollama cloud models send data off the machine; keep them hidden unless asked.
SHOW_CLOUD_MODELS = env.bool("SHOW_CLOUD_MODELS", default=False)

# Defaults used when creating a knowledge base / conversation. Per-object
# values are stored in the database.
DEFAULT_CHUNK_SIZE = env.int("DEFAULT_CHUNK_SIZE", default=900)
DEFAULT_CHUNK_OVERLAP = env.int("DEFAULT_CHUNK_OVERLAP", default=120)
DEFAULT_TOP_K = env.int("DEFAULT_TOP_K", default=4)
DEFAULT_TEMPERATURE = env.float("DEFAULT_TEMPERATURE", default=0.2)
DEFAULT_NUM_CTX = env.int("DEFAULT_NUM_CTX", default=8192)
MAX_UPLOAD_SIZE_MB = env.int("MAX_UPLOAD_SIZE_MB", default=50)

# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Local RAG API",
    "DESCRIPTION": (
        "Local, document-agnostic retrieval-augmented generation over Ollama. "
        "No authentication: bind to 127.0.0.1 only."
    ),
    "VERSION": "2.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_CREDENTIALS = False
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "{levelname} {asctime} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "chromadb": {"level": "WARNING"},
        "httpx": {"level": "WARNING"},
    },
}

# ---------------------------------------------------------------------------
# Admin branding
# ---------------------------------------------------------------------------

ADMIN_SITE_HEADER = "Local RAG"
ADMIN_SITE_TITLE = "Local RAG"
ADMIN_INDEX_TITLE = "Administration"
