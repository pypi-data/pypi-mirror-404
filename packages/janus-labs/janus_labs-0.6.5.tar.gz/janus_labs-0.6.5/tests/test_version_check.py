"""Tests for version update check (JL-230)."""

import json
import sys
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, Mock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli.version_check import (
    get_cache_path,
    read_cache,
    write_cache,
    fetch_latest_version,
    parse_version,
    is_newer,
    check_for_updates,
    CACHE_TTL_HOURS,
)


class TestParseVersion:
    """Tests for version string parsing."""

    def test_simple_version(self):
        assert parse_version("0.6.3") == (0, 6, 3)

    def test_major_version(self):
        assert parse_version("1.0.0") == (1, 0, 0)

    def test_two_part_version(self):
        assert parse_version("1.0") == (1, 0)

    def test_prerelease_suffix_ignored(self):
        assert parse_version("0.6.3a1") == (0, 6, 3)

    def test_dev_suffix_ignored(self):
        assert parse_version("0.6.3.dev1") == (0, 6, 3)

    def test_invalid_version(self):
        assert parse_version("invalid") == (0,)


class TestIsNewer:
    """Tests for version comparison."""

    def test_newer_patch(self):
        assert is_newer("0.6.4", "0.6.3") is True

    def test_newer_minor(self):
        assert is_newer("0.7.0", "0.6.3") is True

    def test_newer_major(self):
        assert is_newer("1.0.0", "0.6.3") is True

    def test_same_version(self):
        assert is_newer("0.6.3", "0.6.3") is False

    def test_older_version(self):
        assert is_newer("0.6.2", "0.6.3") is False

    def test_current_newer(self):
        # User has unreleased dev version
        assert is_newer("0.6.3", "0.6.4") is False


class TestCachePath:
    """Tests for cache path determination."""

    def test_cache_path_contains_expected_components(self):
        """Test that cache path has expected structure."""
        path = get_cache_path()
        assert "janus-labs" in str(path)
        assert "version-cache.json" in str(path)

    def test_cache_path_is_absolute(self):
        """Test cache path is an absolute path."""
        path = get_cache_path()
        assert path.is_absolute()


class TestCacheReadWrite:
    """Tests for cache read/write operations."""

    def test_write_and_read_cache(self, tmp_path):
        with patch("cli.version_check.get_cache_path", return_value=tmp_path / "cache.json"):
            write_cache("0.6.4")
            cached = read_cache()
            assert cached is not None
            assert cached["latest_version"] == "0.6.4"

    def test_read_expired_cache(self, tmp_path):
        cache_file = tmp_path / "cache.json"
        old_time = datetime.now(timezone.utc) - timedelta(hours=CACHE_TTL_HOURS + 1)
        data = {
            "latest_version": "0.6.4",
            "checked_at": old_time.isoformat(),
            "ttl_hours": CACHE_TTL_HOURS,
        }
        cache_file.write_text(json.dumps(data))

        with patch("cli.version_check.get_cache_path", return_value=cache_file):
            cached = read_cache()
            assert cached is None  # Expired cache should return None

    def test_read_valid_cache(self, tmp_path):
        cache_file = tmp_path / "cache.json"
        recent_time = datetime.now(timezone.utc) - timedelta(hours=1)
        data = {
            "latest_version": "0.6.4",
            "checked_at": recent_time.isoformat(),
            "ttl_hours": CACHE_TTL_HOURS,
        }
        cache_file.write_text(json.dumps(data))

        with patch("cli.version_check.get_cache_path", return_value=cache_file):
            cached = read_cache()
            assert cached is not None
            assert cached["latest_version"] == "0.6.4"

    def test_read_missing_cache(self, tmp_path):
        with patch("cli.version_check.get_cache_path", return_value=tmp_path / "nonexistent.json"):
            cached = read_cache()
            assert cached is None

    def test_read_corrupt_cache(self, tmp_path):
        cache_file = tmp_path / "cache.json"
        cache_file.write_text("not valid json")

        with patch("cli.version_check.get_cache_path", return_value=cache_file):
            cached = read_cache()
            assert cached is None


class TestFetchLatestVersion:
    """Tests for PyPI API fetching."""

    @patch("httpx.Client")
    def test_fetch_success(self, mock_client_class):
        mock_response = Mock()
        mock_response.json.return_value = {"info": {"version": "0.6.4"}}
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client_class.return_value = mock_client

        version = fetch_latest_version()
        assert version == "0.6.4"

    @patch("httpx.Client")
    def test_fetch_timeout(self, mock_client_class):
        mock_client_class.side_effect = Exception("timeout")
        version = fetch_latest_version()
        assert version is None

    @patch("httpx.Client")
    def test_fetch_network_error(self, mock_client_class):
        mock_client_class.side_effect = ConnectionError("no network")
        version = fetch_latest_version()
        assert version is None


class TestCheckForUpdates:
    """Integration tests for update check flow."""

    @patch("cli.version_check.read_cache")
    @patch("cli.version_check.print_update_banner")
    def test_shows_banner_when_update_available(self, mock_banner, mock_cache):
        mock_cache.return_value = {"latest_version": "0.6.4"}
        check_for_updates("0.6.3")
        mock_banner.assert_called_once_with("0.6.3", "0.6.4")

    @patch("cli.version_check.read_cache")
    @patch("cli.version_check.print_update_banner")
    def test_no_banner_when_current(self, mock_banner, mock_cache):
        mock_cache.return_value = {"latest_version": "0.6.3"}
        check_for_updates("0.6.3")
        mock_banner.assert_not_called()

    @patch("cli.version_check.read_cache")
    @patch("cli.version_check.fetch_latest_version")
    @patch("cli.version_check.write_cache")
    @patch("cli.version_check.print_update_banner")
    def test_fetches_when_cache_empty(self, mock_banner, mock_write, mock_fetch, mock_cache):
        mock_cache.return_value = None
        mock_fetch.return_value = "0.6.4"

        check_for_updates("0.6.3")

        mock_fetch.assert_called_once()
        mock_write.assert_called_once_with("0.6.4")
        mock_banner.assert_called_once_with("0.6.3", "0.6.4")

    @patch("cli.version_check.read_cache")
    @patch("cli.version_check.fetch_latest_version")
    @patch("cli.version_check.print_update_banner")
    def test_silent_on_fetch_failure(self, mock_banner, mock_fetch, mock_cache):
        mock_cache.return_value = None
        mock_fetch.return_value = None

        # Should not raise, should not print banner
        check_for_updates("0.6.3")
        mock_banner.assert_not_called()
