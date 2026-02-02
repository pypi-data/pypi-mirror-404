"""
Configuration management for PIP-BOY LLM.
Handles loading/saving of user preferences.
"""

import os
import yaml

# Config directory and file paths
CONFIG_DIR = os.path.expanduser("~/.airllm")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.yaml")
HISTORY_PATH = os.path.join(CONFIG_DIR, "history.yaml")

# Default configuration
DEFAULT_CONFIG = {
    "default_model": "mistral-7b",
    "max_file_size": 51200,  # 50KB
    "history_file": HISTORY_PATH,
    "color_mode": "green",  # green, red, cyan, yellow
    "user_name": "VAULT DWELLER",
}

# Color themes
COLOR_THEMES = {
    "green": {
        "primary": "\033[92m",      # Bright green
        "secondary": "\033[32m",    # Dark green
        "accent": "\033[38;5;118m", # Lime
    },
    "red": {
        "primary": "\033[91m",      # Bright red
        "secondary": "\033[31m",    # Dark red
        "accent": "\033[38;5;203m", # Coral
    },
    "cyan": {
        "primary": "\033[96m",      # Bright cyan
        "secondary": "\033[36m",    # Dark cyan
        "accent": "\033[38;5;87m",  # Light cyan
    },
    "yellow": {
        "primary": "\033[93m",      # Bright yellow
        "secondary": "\033[33m",    # Dark yellow/orange
        "accent": "\033[38;5;220m", # Gold
    },
}


def get_theme_colors(theme_name: str = None) -> dict:
    """Get color codes for a theme. Returns green if theme not found."""
    if theme_name is None:
        theme_name = get_config_value("color_mode", "green")
    return COLOR_THEMES.get(theme_name, COLOR_THEMES["green"])


def ensure_config_dir():
    """Create config directory if it doesn't exist."""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)


def load_config() -> dict:
    """
    Load configuration from file.
    Returns default config merged with saved config.
    """
    config = DEFAULT_CONFIG.copy()

    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved_config = yaml.safe_load(f) or {}
                config.update(saved_config)
        except Exception:
            pass  # Use defaults on error

    return config


def save_config(config: dict):
    """Save configuration to file."""
    ensure_config_dir()

    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False)
    except Exception as e:
        raise RuntimeError(f"Failed to save config: {e}")


def get_config_value(key: str, default=None):
    """Get a single config value."""
    config = load_config()
    return config.get(key, default)


def set_config_value(key: str, value):
    """Set a single config value."""
    config = load_config()
    config[key] = value
    save_config(config)
