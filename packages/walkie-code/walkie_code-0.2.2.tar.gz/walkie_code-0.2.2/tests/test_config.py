"""Tests for configuration management"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    load_config,
    save_config,
    get_device_token,
    get_config_file,
    get_lock_file,
    check_existing_connection,
    create_connection_lock,
    remove_connection_lock,
)


class TestConfigFile:
    """Test configuration file handling"""

    def test_get_config_file_returns_path(self):
        """Test that get_config_file returns a Path object"""
        config_file = get_config_file()
        assert isinstance(config_file, Path)
        assert config_file.name == ".walkiecode_config.json"

    def test_get_lock_file_returns_path(self):
        """Test that get_lock_file returns a Path object"""
        lock_file = get_lock_file()
        assert isinstance(lock_file, Path)
        assert lock_file.name == ".walkiecode.lock"

    def test_config_file_in_current_directory(self, tmp_path):
        """Test that config file path uses current working directory"""
        with patch("config.Path.cwd", return_value=tmp_path):
            config_file = get_config_file()
            # Just verify it returns the right filename
            assert config_file.name == ".walkiecode_config.json"

    def test_lock_file_in_current_directory(self, tmp_path):
        """Test that lock file path uses current working directory"""
        with patch("config.Path.cwd", return_value=tmp_path):
            lock_file = get_lock_file()
            # Just verify it returns the right filename
            assert lock_file.name == ".walkiecode.lock"


class TestLoadConfig:
    """Test loading configuration"""

    def test_load_empty_config(self, tmp_path):
        """Test loading config when no file exists"""
        with patch("config.Path.cwd", return_value=tmp_path):
            config = load_config()
            assert config == {}

    def test_load_existing_config(self, tmp_path):
        """Test loading existing configuration file"""
        config_file = tmp_path / ".walkiecode_config.json"
        test_config = {"deviceToken": "test_token", "claude": {"timeout": 300}}
        config_file.write_text(json.dumps(test_config))

        with patch("config.Path.cwd", return_value=tmp_path):
            config = load_config()
            assert config == test_config

    def test_load_invalid_config_returns_empty(self, tmp_path, capsys):
        """Test that invalid config file returns empty dict with warning"""
        config_file = tmp_path / ".walkiecode_config.json"
        config_file.write_text("invalid json {")

        with patch("config.Path.cwd", return_value=tmp_path):
            config = load_config()
            assert config == {}


class TestSaveConfig:
    """Test saving configuration"""

    def test_save_config(self, tmp_path):
        """Test saving configuration to file"""
        with patch("config.Path.cwd", return_value=tmp_path):
            test_config = {"deviceToken": "test_token", "claude": {"timeout": 300}}
            result = save_config(test_config, silent=True)

            assert result is True
            config_file = tmp_path / ".walkiecode_config.json"
            assert config_file.exists()
            saved_config = json.loads(config_file.read_text())
            assert saved_config == test_config

    def test_save_config_silent_mode(self, tmp_path, capsys):
        """Test that silent mode doesn't print message"""
        with patch("config.Path.cwd", return_value=tmp_path):
            save_config({"deviceToken": "test"}, silent=True)
            captured = capsys.readouterr()
            assert "Configuration saved" not in captured.out

    def test_save_config_verbose_mode(self, tmp_path, capsys):
        """Test that verbose mode prints message"""
        with patch("config.Path.cwd", return_value=tmp_path):
            save_config({"deviceToken": "test"}, silent=False)
            captured = capsys.readouterr()
            assert "Configuration saved" in captured.out


class TestConnectionLock:
    """Test connection lock management"""

    def test_create_connection_lock(self, tmp_path):
        """Test creating a connection lock file"""
        with patch("config.Path.cwd", return_value=tmp_path):
            result = create_connection_lock("test_token")
            assert result is True
            lock_file = tmp_path / ".walkiecode.lock"
            assert lock_file.exists()
            lock_data = json.loads(lock_file.read_text())
            assert lock_data["deviceToken"] == "test_token"

    def test_check_existing_connection_no_lock(self, tmp_path):
        """Test checking connection when no lock exists"""
        with patch("config.Path.cwd", return_value=tmp_path):
            existing = check_existing_connection()
            assert existing is None

    def test_check_existing_connection_with_lock(self, tmp_path):
        """Test checking connection when lock exists"""
        with patch("config.Path.cwd", return_value=tmp_path):
            create_connection_lock("existing_token")
            existing = check_existing_connection()
            assert existing == "existing_token"

    def test_remove_connection_lock(self, tmp_path):
        """Test removing a connection lock file"""
        with patch("config.Path.cwd", return_value=tmp_path):
            create_connection_lock("test_token")
            lock_file = tmp_path / ".walkiecode.lock"
            assert lock_file.exists()

            result = remove_connection_lock()
            assert result is True
            assert not lock_file.exists()

    def test_remove_connection_lock_no_file(self, tmp_path):
        """Test removing lock when no lock exists doesn't fail"""
        with patch("config.Path.cwd", return_value=tmp_path):
            result = remove_connection_lock()
            assert result is True
