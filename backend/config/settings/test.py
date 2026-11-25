"""Test-suite Django settings backed by PostgreSQL."""

import os

import dj_database_url

from .base import *  # noqa: F403

DEBUG = False
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    os.getenv("DATABASE_URL", "postgresql://rankit:rankit_dev_password@localhost:5432/rankit"),
)
DATABASES = {
    "default": dj_database_url.parse(TEST_DATABASE_URL, conn_max_age=0),
}
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
