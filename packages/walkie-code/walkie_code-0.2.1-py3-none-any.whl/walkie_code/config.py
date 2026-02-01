"""Configuration management for WalkieCode"""

import json
from pathlib import Path

DEFAULT_ENDPOINT = "wss://qcc76l29g6.execute-api.eu-central-1.amazonaws.com/prod/"

# Configuration stored in current working directory
def get_config_file():
    """Get config file path in current working directory"""
    return Path.cwd() / ".walkiecode_config.json"

def get_lock_file():
    """Get connection lock file path in current working directory"""
    return Path.cwd() / ".walkiecode.lock"

# Default Claude CLI settings
DEFAULT_CLAUDE_SETTINGS = {
    "skip_permissions": True,  # Auto-accept file edits by default
    "timeout": 300,            # Default timeout in seconds
    "model": "claude-sonnet-4-20250514",  # Default model
    "permission_mode": "acceptEdits"      # Permission mode when skip_permissions is True
}


def load_config():
    """Load configuration from file"""
    config_file = get_config_file()
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
    return {}


def save_config(config, silent=False):
    """Save configuration to file"""
    config_file = get_config_file()
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        if not silent:
            print(f"✓ Configuration saved to {config_file}")
        return True
    except Exception as e:
        print(f"Warning: Could not save config file: {e}")
        return False


def get_device_token(config):
    """Get device token from config or prompt user"""
    device_token = config.get('deviceToken')

    if not device_token:
        print("=" * 60)
        print("WalkieCode Desktop Client")
        print("=" * 60)
        print()
        print("Enter device token from iOS app:")
        device_token = input("Device Token: ").strip()
        print()

        if device_token:
            config['deviceToken'] = device_token
            save_config(config)

    return device_token


def check_existing_connection():
    """Check if another connection is already active with the same token"""
    lock_file = get_lock_file()
    if lock_file.exists():
        try:
            with open(lock_file, 'r') as f:
                lock_data = json.load(f)
                existing_token = lock_data.get('deviceToken')
                return existing_token
        except Exception:
            pass
    return None


def create_connection_lock(device_token):
    """Create a lock file indicating active connection"""
    lock_file = get_lock_file()
    try:
        with open(lock_file, 'w') as f:
            json.dump({'deviceToken': device_token}, f)
        return True
    except Exception as e:
        print(f"Warning: Could not create lock file: {e}")
        return False


def remove_connection_lock():
    """Remove the connection lock file"""
    lock_file = get_lock_file()
    try:
        if lock_file.exists():
            lock_file.unlink()
        return True
    except Exception as e:
        print(f"Warning: Could not remove lock file: {e}")
        return False


def get_claude_settings(config):
    """Get Claude CLI settings with defaults"""
    claude_config = config.get('claude', {})

    # Merge with defaults
    settings = DEFAULT_CLAUDE_SETTINGS.copy()
    settings.update(claude_config)

    return settings
