# Authentication package
# Note: Most auth functions remain in server.py due to dependencies on
# app-level configurations (db, security, cipher_suite).
# This package contains helper functions that can be safely extracted.

from .password import hash_password, verify_password
