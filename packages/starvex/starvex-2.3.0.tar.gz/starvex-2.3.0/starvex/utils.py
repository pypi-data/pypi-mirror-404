"""
Starvex Utilities
"""

import os
import re
import secrets
import logging
from typing import Dict, Any


def generate_api_key(prefix: str = "sv_live_") -> str:
    """Generate a new API key"""
    random_part = secrets.token_urlsafe(32)
    return f"{prefix}{random_part}"


def validate_api_key_format(key: str) -> bool:
    """Validate API key format"""
    pattern = r"^sv_(live|test)_[A-Za-z0-9_-]{32,}$"
    return bool(re.match(pattern, key))


def redact_sensitive_data(text: str) -> str:
    """Redact PII from text"""
    # Email
    text = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL]", text)
    # Phone
    text = re.sub(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[PHONE]", text)
    # SSN
    text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]", text)
    # Credit card
    text = re.sub(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "[CARD]", text)
    return text


def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def get_config_from_env() -> Dict[str, Any]:
    """Get configuration from environment variables"""
    return {
        "api_key": os.environ.get("STARVEX_API_KEY"),
        "api_host": os.environ.get(
            "STARVEX_API_HOST", "https://decqadhkqnacujoyirkh.supabase.co/functions/v1"
        ),
        "redact_pii": os.environ.get("STARVEX_REDACT_PII", "").lower() == "true",
        "log_level": os.environ.get("STARVEX_LOG_LEVEL", "INFO"),
    }


def get_config_path() -> str:
    """Get the path to the config file"""
    if os.name == "nt":  # Windows
        config_dir = os.path.join(os.environ.get("APPDATA", ""), "starvex")
    else:  # Unix/Linux/Mac
        config_dir = os.path.join(os.path.expanduser("~"), ".config", "starvex")

    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "config.json")


def save_api_key(api_key: str) -> None:
    """Save API key to config file"""
    import json

    config_path = get_config_path()
    config = {}

    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)

    config["api_key"] = api_key

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)


def load_api_key() -> str | None:
    """Load API key from config file"""
    import json

    config_path = get_config_path()

    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
            return config.get("api_key")

    return None
