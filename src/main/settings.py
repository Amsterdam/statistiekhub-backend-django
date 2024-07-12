"""
Django settings for statistiek_hub project.

Generated by 'django-admin startproject' using Django 4.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
import os
from pathlib import Path
from urllib.parse import urljoin

from azure.identity import DefaultAzureCredential, WorkloadIdentityCredential

from .azure_settings import Azure

azure = Azure()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", False)

ALLOWED_HOSTS = ["*"]
X_FRAME_OPTIONS = "ALLOW-FROM *"
INTERNAL_IPS = ("127.0.0.1", "0.0.0.0")
DATA_UPLOAD_MAX_MEMORY_SIZE = (
    1024 * 1024 * 20
)  # max upload size; 20MB (instead of the default 2.5MB)
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240  # higher than the count of fields

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "statistiek_hub",
    "referentie_tabellen",
    "publicatie_tabellen",
    "import_export",
    "import_export_job",
    "leaflet",
]

# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
]
THIRD_PARTY_APPS = [
    "import_export",
    "leaflet",
    "storages",
]
LOCAL_APPS = [
    "statistiek_hub",
    "referentie_tabellen",
    "publicatie_tabellen",
    "import_export_job",
    "job_consumer",
]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# import_export_job
def resource_observation():
    from statistiek_hub.resources.observation_resource import ObservationResource
    return ObservationResource

def resource_spatialdimension():
    from statistiek_hub.resources.spatial_dimension_resource import (
        SpatialDimensionResource,
    )
    return SpatialDimensionResource


IMPORT_EXPORT_JOB_MODELS = {
    "Observation": {
        "app_label": "statistiek_hub",
        "model_name": "Observation",
        "resource": resource_observation,
    },
    "SpatialDimension": {
        "app_label": "statistiek_hub",
        "model_name": "SpatialDimension",
        "resource": resource_spatialdimension,
    },
}

ROOT_URLCONF = "main.urls"
BASE_URL = os.getenv("BASE_URL", "")
FORCE_SCRIPT_NAME = BASE_URL

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

WSGI_APPLICATION = "main.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASE_HOST = os.getenv("DATABASE_HOST", "database")
DATABASE_NAME = os.getenv("DATABASE_NAME", "statistiek_hub")
DATABASE_USER = os.getenv("DATABASE_USER", "statistiek_hub")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "insecure")
DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
SCHEMA = os.getenv("DB_SCHEMA", "public")
DATABASE_OPTIONS = {"options": f"-c search_path={SCHEMA}", "sslmode": "allow", "connect_timeout": 5}


if "azure.com" in DATABASE_HOST:
    DATABASE_PASSWORD = azure.auth.db_password
    DATABASE_OPTIONS["sslmode"] = "require"

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": DATABASE_NAME,
        "USER": DATABASE_USER,
        "PASSWORD": DATABASE_PASSWORD,
        "HOST": DATABASE_HOST,
        "CONN_MAX_AGE": 60 * 5,
        "PORT": DATABASE_PORT,
        "OPTIONS": DATABASE_OPTIONS,
    },
}

# Django-storages for Django > 4.2
STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

# -----Azure Storageaccount settings
if os.getenv("AZURE_FEDERATED_TOKEN_FILE"):
    credential = WorkloadIdentityCredential()
    STORAGE_AZURE = {
        "default": {
            "BACKEND": "storages.backends.azure_storage.AzureStorage",
            "OPTIONS": {
                "token_credential": credential,
                "account_name": os.getenv("AZURE_STORAGE_ACCOUNT_NAME"),
                "azure_container": "django",
            },
        },
    }
    STORAGES |= STORAGE_AZURE #update storages with storage_azure

if os.getenv("AZURITE_STORAGE_CONNECTION_STRING"):
    print('---------------in azurite storage')
    # create container slechts eenmalig
    from azure.storage.blob import BlobServiceClient
    blob_service_client = BlobServiceClient.from_connection_string(os.getenv("AZURITE_STORAGE_CONNECTION_STRING"))
    container_client = blob_service_client.get_container_client("django")
    if not container_client.exists():
        container_client.create_container()
    #connect django
    STORAGE_AZURE = {
        "default": {
            "BACKEND": "storages.backends.azure_storage.AzureStorage",
            "OPTIONS": {
                "connection_string": os.getenv("AZURITE_STORAGE_CONNECTION_STRING"),
                "azure_container": "django",
            },
        },
    }
    STORAGES |= STORAGE_AZURE #update storages with storage_azure

# -----Queue
AZURITE_QUEUE_CONNECTION_STRING = os.getenv("AZURITE_QUEUE_CONNECTION_STRING")
QUEUE_ACCOUNT_URL = os.getenv("QUEUE_ACCOUNT_URL")
JOB_QUEUE_NAME = "job-queue"


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Europe/Amsterdam"

USE_I18N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = urljoin(f"{BASE_URL}/", "static/")
STATIC_ROOT = "static"


MEDIA_ROOT = os.path.join(BASE_DIR, "media").replace("\\", "/")
MEDIA_URL = "/media/"


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache",
        "TIMEOUT": 60,
    }
}

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


FIXTURE_DIRS = [os.path.join(BASE_DIR, "fixtures")]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}


# TODO: leaflet lijkt alleen te werken met CRS WebMercator. Misschien is mogelijk SRID/CRS om te zetten naar RD 28992?
LEAFLET_CONFIG = {
    "TILES": [
        (
            "Amsterdam",
            "https://t1.data.amsterdam.nl/topo_wm_light/{z}/{x}/{y}.png",
            {
                "attribution": 'Kaartgegevens &copy; <a href="https://data.amsterdam.nl/">Gemeente Amsterdam </a>'
            },
        ),
    ],
    "DEFAULT_CENTER": (4.9020727, 52.3717204),
    "DEFAULT_ZOOM": 12,
    "MIN_ZOOM": 11,
    "MAX_ZOOM": 21,
    "SPATIAL_EXTENT": (3.2, 50.75, 7.22, 53.7),
    "RESET_VIEW": False,
}
