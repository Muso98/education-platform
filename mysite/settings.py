from pathlib import Path
import os
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-8w!gq*yfbr9ad7w&a_hlvgub$i$(3w_f3b2n14td*ka1s(8ou4'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'widget_tweaks',
    'csp',

    # Local apps
    'core',
    'ui',

]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "csp.middleware.CSPMiddleware",                # ⬅️ django-csp
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = 'mysite.urls'
WSGI_APPLICATION = "mysite.wsgi.application"


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'ui' / 'templates'],
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



# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "uz"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("uz", _("O‘zbekcha")),
    ("ru", _("Ruscha")),
    ("en", _("Inglizcha")),
]
LOCALE_PATHS = [BASE_DIR / "locale"]


# Static files (CSS, JavaScript, Images)
# --- STATIC ---
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "ui" / "static"]   # agar umumiy 'static' papkangiz bo‘lsa o‘shanga ko‘rsating
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ────────────────────────────────────────────────────────────────────────────────
# Auth redirects
# ────────────────────────────────────────────────────────────────────────────────
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"

# ────────────────────────────────────────────────────────────────────────────────
# Email (dev)
# ────────────────────────────────────────────────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "noreply@example.com"
CONTACT_TO_EMAIL = "admin@example.com"


X_FRAME_OPTIONS = 'SAMEORIGIN'

# ─── django-csp (v4+) yagona konfiguratsiya ───────────────────────────────────
CONTENT_SECURITY_POLICY = {
    # REPORT_ONLY=True qilsangiz faqat ogohlantiradi (bloklamaydi) — debug uchun qulay
    "REPORT_ONLY": False,

    "DIRECTIVES": {
        # Bazaviy ruxsatlar
        "default-src": ("'self'",),
        "base-uri": ("'self'",),
        "form-action": ("'self'",),
        "object-src": ("'none'",),
        # Kimlar sizning saytni iframe ichiga qo‘ya oladi
        "frame-ancestors": ("'self'",),

        # Skriptlar (YouTube, Gstatic, jQuery/Bootstrap/CDN)
        "script-src": (
            "'self'",
            "https://www.youtube.com",
            "https://www.gstatic.com",
            "https://code.jquery.com",
            "https://cdn.jsdelivr.net",
        ),

        # Stil (inline + jsDelivr + Google Fonts CSS)
        "style-src": (
            "'self'",
            "'unsafe-inline'",
            "https://cdn.jsdelivr.net",
            "https://fonts.googleapis.com",
            "https://cdnjs.cloudflare.com",  # <— YANGI

        ),


        # Shriftlar (Google Fonts)
        "font-src": (
            "'self'",
            "https://fonts.gstatic.com",
            "data:",
            "https://cdn.jsdelivr.net",  # <— YANGI (Bootstrap Icons .woff2 shu yerdan)
            "https://cdnjs.cloudflare.com",
        ),

        # Rasmlar (local, data/blob va tashqi)
        "img-src": (
            "'self'",
            "data:",
            "blob:",
            "https:",
        ),

        # Iframe (YouTube/Vimeo/Office viewer + lokal host)
        "frame-src": (
            "'self'",
            "http://127.0.0.1:8000",
            "https://www.youtube.com",
            "https://www.youtube-nocookie.com",
            "https://player.vimeo.com",
            "https://view.officeapps.live.com",
        ),

        # AJAX/fetch/WebSocket (dev-server + tashqi xizmatlar)
        "connect-src": (
            "'self'",
            "http://127.0.0.1:8000",
            "https://www.youtube.com",
            "https://www.google.com",
        ),
    },
}


# ────────────────────────────────────────────────────────────────────────────────
# Logging (dev uchun qulay)
# ────────────────────────────────────────────────────────────────────────────────
# LOGGING = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "handlers": {"console": {"class": "logging.StreamHandler"}},
#     "loggers": {
#         "django.request": {"handlers": ["console"], "level": "DEBUG"},
#         "django.template": {"handlers": ["console"], "level": "DEBUG"},
#     },
# }



