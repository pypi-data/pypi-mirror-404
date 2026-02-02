import argparse
from unittest.mock import patch

import pytest

from xsget import config


def create_config_file(path, content):
    with open(path, "w") as f:
        f.write(content)


def test_load_config_success(tmp_path):
    config_path = tmp_path / "test_config.toml"
    content = 'config_version = 3\nurl = "http://example.com"'
    create_config_file(config_path, content)

    args = argparse.Namespace(config=str(config_path), generate_config=None)

    dummy_template = 'config_version = 3\nurl = "default"'

    with patch("xsget.config.read_text", return_value=dummy_template):
        result = config.load_or_create_config(args, "xsget")

    assert result["url"] == "http://example.com"
    assert result["config_version"] == 3


def test_load_config_corrupted(tmp_path):
    config_path = tmp_path / "empty_config.toml"
    create_config_file(config_path, "")

    args = argparse.Namespace(config=str(config_path), generate_config=None)

    with pytest.raises(config.ConfigFileCorruptedError):
        config.load_or_create_config(args, "xsget")


def test_create_config_exists(tmp_path):
    config_path = tmp_path / "existing.toml"
    create_config_file(config_path, "content")

    args = argparse.Namespace(config=None, generate_config=str(config_path))

    with pytest.raises(config.ConfigFileExistsError):
        config.load_or_create_config(args, "xsget")


def test_upgrade_config(tmp_path):
    config_path = tmp_path / "old_config.toml"
    # Old version
    create_config_file(
        config_path, 'config_version = 1\nurl = "http://old.com"'
    )

    args = argparse.Namespace(config=str(config_path), generate_config=None)

    # Template has version 3
    dummy_template = 'config_version = 3\nurl = "default"'

    with patch("xsget.config.read_text", return_value=dummy_template):
        # We need to mock datetime to have deterministic backup filename
        with patch("xsget.config.dt") as mock_dt:
            mock_dt.now.return_value.strftime.return_value = "20000101_120000"

            result = config.load_or_create_config(args, "xsget")

    # Check if backup was created
    backup_path = tmp_path / "old_config_20000101_120000_backup.toml"
    assert backup_path.exists()
    assert "config_version = 1" in backup_path.read_text()

    # Check if original file was updated
    assert config_path.exists()
    new_content = config_path.read_text()
    assert "config_version = 3" in new_content
    # The upgrade process loads old config into Namespace, calls _create_config
    # _create_config loads template, overrides with values from Namespace.
    # So 'url' should be preserved if it was in config_dict.
    # So 'url' should be preserved if it was in config_dict.
    assert 'url = "http://old.com"' in new_content


def test_generating_default_config_file(script_runner):
    default_url = "http://localhost"
    ret = script_runner("xsget", default_url, "-g")
    assert "Create config file: xsget.toml" in ret.stdout
    assert (
        "Cannot connect to host localhost:80 "
        "ssl:default [Connect call failed ('127.0.0.1', 80)]" in ret.stdout
    )
