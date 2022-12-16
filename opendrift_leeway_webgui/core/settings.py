"""
Django settings for opendrift-leeway-webgui project.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from .logging_formatter import ColorFormatter, RequestFormatter
from .utils import strtobool

###################
# CUSTOM SETTINGS #
###################

#: Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

#: The path to the simulation script passed to the opendrift docker container
SIMULATION_SCRIPT_PATH = BASE_DIR / "simulation.py"

#: Number of drifters simulated
OPENDRIFT_NUMBER_DRIFTERS = int(os.environ.get("LEEWAY_OPENDRIFT_NUMBER_DRIFTERS", 100))


########################
# DJANGO CORE SETTINGS #
########################

#: A boolean that turns on/off debug mode (see :setting:`django:DEBUG`)
#:
#: .. warning::
#:     Never deploy a site into production with :setting:`DEBUG` turned on!
DEBUG = bool(strtobool(os.environ.get("LEEWAY_DEBUG", "False")))

#: The secret key for this particular Django installation (see :setting:`django:SECRET_KEY`)
#:
#: .. warning::
#:     Provide a key via the environment variable ``LEEWAY_SECRET_KEY`` in production and keep it secret!
SECRET_KEY = os.environ.get("LEEWAY_SECRET_KEY", "dummy" if DEBUG else "")

#: This is a security measure to prevent HTTP Host header attacks, which are possible even under many seemingly-safe
#: web server configurations (see :setting:`django:ALLOWED_HOSTS` and :ref:`django:host-headers-virtual-hosting`)
ALLOWED_HOSTS = [".localhost", "127.0.0.1", "[::1]"] + [
    x.strip() for x in os.environ.get("LEEWAY_ALLOWED_HOSTS", "").splitlines() if x
]

#: Enabled applications (see :setting:`django:INSTALLED_APPS`)
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "opendrift_leeway_webgui.leeway",
]

#: Activated middlewares (see :setting:`django:MIDDLEWARE`)
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

#: Default URL dispatcher (see :setting:`django:ROOT_URLCONF`)
ROOT_URLCONF = "opendrift_leeway_webgui.core.urls"

#: Config for HTML templates (see :setting:`django:TEMPLATES`)
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
            ]
        },
    }
]

#: WSGI (Web Server Gateway Interface) config (see :setting:`django:WSGI_APPLICATION`)
WSGI_APPLICATION = "opendrift_leeway_webgui.core.wsgi.application"

#: The list of validators that are used to check the strength of user’s passwords
#: (see :setting:`django:AUTH_PASSWORD_VALIDATORS` and :ref:`django:password-validation`)
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

#: The URL where requests are redirected after login (see :setting:`django:LOGIN_REDIRECT_URL`)
LOGIN_REDIRECT_URL = "/"


############
# DATABASE #
############

#: A dictionary containing the settings for all databases to be used with this Django installation
#: (see :setting:`django:DATABASES`)
DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}
}

#: Default primary key field type to use for models that don’t have a field with
#: :attr:`primary_key=True <django.db.models.Field.primary_key>`. (see :setting:`django:DEFAULT_AUTO_FIELD`)
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


########################
# INTERNATIONALIZATION #
########################

#: A string representing the language slug for this installation
#: (see :setting:`django:LANGUAGE_CODE` and :doc:`django:topics/i18n/index`)
LANGUAGE_CODE = os.environ.get("LEEWAY_LANGUAGE_CODE", "en-us")

#: A string representing the time zone for this installation
#: (see :setting:`django:TIME_ZONE` and :doc:`django:topics/i18n/index`)
TIME_ZONE = "UTC"

#: A boolean that specifies whether Django’s translation system should be enabled
#: (see :setting:`django:USE_I18N` and :doc:`django:topics/i18n/index`)
USE_I18N = True

#: A boolean that specifies if localized formatting of data will be enabled by default or not
#: (see :setting:`django:USE_L10N` and :doc:`django:topics/i18n/index`)
USE_L10N = True

#: A boolean that specifies if datetimes will be timezone-aware by default or not
#: (see :setting:`django:USE_TZ` and :doc:`django:topics/i18n/index`)
USE_TZ = True


################
# STATIC FILES #
################

#: URL to use in development when referring to static files located in :setting:`STATICFILES_DIRS`
#: (see :setting:`django:STATIC_URL` and :doc:`Managing static files <django:howto/static-files/index>`)
STATIC_URL = "/static/"

#: The absolute path to the output directory where :mod:`django.contrib.staticfiles` will put static files for
#: deployment (see :setting:`django:STATIC_ROOT` and :doc:`Managing static files <django:howto/static-files/index>`)
#: In debug mode, this is not required since :mod:`django.contrib.staticfiles` can directly serve these files.
STATIC_ROOT = os.environ.get("LEEWAY_STATIC_ROOT")

#: URL where simulations are served
SIMULATION_URL = "/simulations/"

#: The path where simulation results are stored
SIMULATION_ROOT = os.environ.get(
    "LEEWAY_SIMULATION_ROOT", os.path.join(BASE_DIR, "simulation")
)

#: The output path of simulation results
SIMULATION_OUTPUT = os.path.join(SIMULATION_ROOT, "output")

#: Number of days for keeping simulations and results.
SIMULATION_RETENTION = int(os.environ.get("LEEWAY_SIMULATION_RETENTION", 7))


###########
# LOGGING #
###########

#: The log level for opendrift-leeway-webgui django apps
LOG_LEVEL = os.environ.get("LEEWAY_LOG_LEVEL", "DEBUG" if DEBUG else "INFO")

#: The log level for the syslog
SYS_LOG_LEVEL = "INFO"

#: The log level for dependencies
DEPS_LOG_LEVEL = os.environ.get("LEEWAY_DEPS_LOG_LEVEL", "INFO" if DEBUG else "WARN")

#: The file path of the logfile. Needs to be writable by the application.
LOGFILE = os.environ.get(
    "LEEWAY_LOGFILE", os.path.join(BASE_DIR, "opendrift-leeway-webgui.log")
)

#: Logging configuration dictionary (see :setting:`django:LOGGING`)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "()": RequestFormatter,
            "format": "{asctime} \x1b[1m{levelname}\x1b[0m {name} - {message}",
            "datefmt": "%b %d %H:%M:%S",
            "style": "{",
        },
        "console-colored": {
            "()": ColorFormatter,
            "format": "{asctime} {levelname} {name} - {message}",
            "datefmt": "%b %d %H:%M:%S",
            "style": "{",
        },
        "logfile": {
            "()": RequestFormatter,
            "format": "{asctime} {levelname:7} {name} - {message}",
            "datefmt": "%b %d %H:%M:%S",
            "style": "{",
        },
    },
    "filters": {"require_debug_true": {"()": "django.utils.log.RequireDebugTrue"}},
    "handlers": {
        "console": {
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
        "console-colored": {
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "console-colored",
        },
        "logfile": {
            "class": "logging.FileHandler",
            "filename": LOGFILE,
            "formatter": "logfile",
        },
    },
    "loggers": {
        # Loggers of opendrift-leeway-webgui django apps
        "opendrift_leeway_webgui": {
            "handlers": ["console-colored", "logfile"],
            "level": LOG_LEVEL,
        },
        # Loggers of dependencies
        "celery": {"handlers": ["console", "logfile"], "level": DEPS_LOG_LEVEL},
        "django": {"handlers": ["console", "logfile"], "level": DEPS_LOG_LEVEL},
        "dms2dec": {"handlers": ["console", "logfile"], "level": DEPS_LOG_LEVEL},
        "redis": {"handlers": ["console", "logfile"], "level": DEPS_LOG_LEVEL},
    },
}


##########
# CELERY #
##########

#: Configure Celery to use a custom time zone. The timezone value can be any time zone supported by the pytz library.
#: If not set the UTC timezone is used. For backwards compatibility there is also a CELERY_ENABLE_UTC setting,
#: and this is set to false the system local timezone is used instead.
CELERY_TIMEZONE = "UTC"

#: If True the task will report its status as ``started`` when the task is executed by a worker.
#: The default value is False as the normal behavior is to not report that level of granularity.
#: Tasks are either pending, finished, or waiting to be retried.
#: Having a ``started`` state can be useful for when there are long running tasks
#: and there’s a need to report what task is currently running.
CELERY_TASK_TRACK_STARTED = True

#: Task hard time limit in seconds. The worker processing the task will be killed
#: and replaced with a new one when this is exceeded.
CELERY_TASK_TIME_LIMIT = 30 * 60

#: Default broker URL.
CELERY_BROKER_URL = "redis://localhost:6379/0"

#: The backend used to store task results (tombstones). Disabled by default.
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"


##########
# EMAILS #
##########

#: The backend to use for sending emails (see :setting:`django:EMAIL_BACKEND` and :doc:`django:topics/email`)
EMAIL_BACKEND = (
    "django.core.mail.backends."
    + os.environ.get("LEEWAY_EMAIL_BACKEND", "console" if DEBUG else "smtp")
    + ".EmailBackend"
)

#: The email address that error messages come from (see :setting:`django:SERVER_EMAIL`)
SERVER_EMAIL = os.environ.get("LEEWAY_SERVER_EMAIL")

#: Default email address to use for various automated correspondence from the site manager(s)
#: (see :setting:`django:DEFAULT_FROM_EMAIL`)
DEFAULT_FROM_EMAIL = SERVER_EMAIL

#: The host to use for sending email (see :setting:`django:EMAIL_HOST`)
EMAIL_HOST = os.environ.get("LEEWAY_EMAIL_HOST", "localhost")

#: Password to use for the SMTP server defined in :attr:`~LEEWAY.core.settings.EMAIL_HOST`
#: (see :setting:`django:EMAIL_HOST_PASSWORD`). If empty, Django won’t attempt authentication.
EMAIL_HOST_PASSWORD = os.environ.get("LEEWAY_EMAIL_HOST_PASSWORD")

if EMAIL_HOST_PASSWORD and not SERVER_EMAIL:
    raise ImproperlyConfigured(
        "You have set an `EMAIL_HOST_PASSWORD`, but `SERVER_EMAIL` is missing."
    )

#: Username to use for the SMTP server defined in :attr:`~LEEWAY.core.settings.EMAIL_HOST`
#: (see :setting:`django:EMAIL_HOST_USER`). If empty, Django won’t attempt authentication.
EMAIL_HOST_USER = os.environ.get("LEEWAY_EMAIL_HOST_USER", SERVER_EMAIL)

#: Port to use for the SMTP server defined in :attr:`~LEEWAY.core.settings.EMAIL_HOST`
#: (see :setting:`django:EMAIL_PORT`)
EMAIL_PORT = int(os.environ.get("LEEWAY_EMAIL_PORT", 587))

#: Whether to use a TLS (secure) connection when talking to the SMTP server.
#: This is used for explicit TLS connections, generally on port 587.
#: (see :setting:`django:EMAIL_USE_TLS`)
EMAIL_USE_TLS = bool(strtobool(os.environ.get("LEEWAY_EMAIL_USE_TLS", "True")))

#: Whether to use an implicit TLS (secure) connection when talking to the SMTP server.
#: In most email documentation this type of TLS connection is referred to as SSL. It is generally used on port 465.
#: (see :setting:`django:EMAIL_USE_SSL`)
EMAIL_USE_SSL = bool(strtobool(os.environ.get("LEEWAY_EMAIL_USE_SSL", "False")))
