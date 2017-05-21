"""
Django settings for PyHardLinkBackup project.

Generated by 'django-admin startproject' using Django 1.8.8.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os


from PyHardLinkBackup.phlb.config import phlb_config as _phlb_config

# _phlb_config.print_config()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Username/password for PyHardLinkBackup.backup_app.middleware.AlwaysLoggedInAsSuperUser
DEFAULT_USERNAME="AutoLoginUser"
DEFAULT_USERPASS="no password needed!"

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'PyHardLinkBackup.backup_app',
)
ROOT_URLCONF = 'PyHardLinkBackup.django_project.urls'
WSGI_APPLICATION = 'PyHardLinkBackup.django_project.wsgi.application'


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'no-secet'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


try:
    import django_nose
except ImportError:
    pass
else:
    INSTALLED_APPS += ('django_nose',)
    TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
    del(django_nose)


MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    # WARNING:
    # This will 'disable' the authentication, because
    # the default user will always be logged in.
    # But only if phlb_config["ENABLE_AUTO_LOGIN"] == True
    "PyHardLinkBackup.backup_app.middleware.AlwaysLoggedInAsSuperUser",

    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': _phlb_config.database_name,
        'TEST_NAME': ":memory:"
    }
}
print(("Use Database file: '%s'" % DATABASES["default"]["NAME"]))

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

# https://docs.djangoproject.com/en/1.8/ref/settings/#std:setting-LANGUAGE_CODE
LANGUAGE_CODE = _phlb_config.language_code

USE_TZ = False
TIME_ZONE = 'UTC'

USE_I18N = True
USE_L10N = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'

import tempfile
fd, LOG_FILEPATH = tempfile.mkstemp(prefix="PyHardLinkBackup_", suffix=".log")
print(("temp log file: %s" % LOG_FILEPATH))
with open(fd, "w") as f:
    f.write("\n\n")
    f.write("_"*79)
    f.write("\n")
    f.write("Start low level logging from: %s\n" % __file__)
    f.write("\n")

#CRITICAL 	50
#ERROR 	    40
#WARNING 	30
#INFO 	    20
#DEBUG 	    10
#NOTSET 	0
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    # "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": _phlb_config.logging_console_level,
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": LOG_FILEPATH,
            "level": _phlb_config.logging_file_level,
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": False,
        },
        "phlb": {
            "handlers": ["file", "console"],
            "propagate": False,
        },
    },
}
