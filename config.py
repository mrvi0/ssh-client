"""
Configuration settings for SSH Client
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Database settings
DATABASE_PATH = BASE_DIR / "instance" / "ssh_client.db"

# Web server settings
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", "5000"))
WEB_DEBUG = os.getenv("WEB_DEBUG", "True").lower() == "true"

# Admin settings
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@localhost")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
ADMIN_ENABLED = os.getenv("ADMIN_ENABLED", "True").lower() == "true"

# Security settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-jwt-secret-key-change-this")
JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "3600"))  # 1 hour

# Encryption settings
ENCRYPTION_KEY_FILE = BASE_DIR / "instance" / ".encryption_key"

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = BASE_DIR / "ssh_client.log"

# SSH settings
SSH_TIMEOUT = int(os.getenv("SSH_TIMEOUT", "30"))
SSH_MAX_CONNECTIONS = int(os.getenv("SSH_MAX_CONNECTIONS", "10"))

# UI settings
UI_THEME = os.getenv("UI_THEME", "clam")
UI_FONT_SIZE = int(os.getenv("UI_FONT_SIZE", "10"))
UI_WINDOW_WIDTH = int(os.getenv("UI_WINDOW_WIDTH", "1400"))
UI_WINDOW_HEIGHT = int(os.getenv("UI_WINDOW_HEIGHT", "900"))

# Development settings
DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "False").lower() == "true" 