"""
Test settings that reuse the main settings but force the test DB
to be a file on disk so it can be inspected after test runs.

Usage: manage.py test --settings=config.settings_test --keepdb
"""
from .settings import *  # noqa: F401,F403

from pathlib import Path

TEST_DB_PATH = Path(__file__).resolve().parent.parent / 'test_db.sqlite3'

DATABASES['default']['TEST'] = {
    'NAME': str(TEST_DB_PATH),
}

DEBUG = True
