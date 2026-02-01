"""Tests for file processor - includes error condition tests."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from src.file_processor import (
    read_json_file,
    fetch_json_from_url,
    process_config,
    batch_process,
)


class TestReadJsonFile:
    """Tests for read_json_file function."""

    def test_valid_json_file(self, tmp_path):
        """Successfully reads valid JSON file."""
        test_file = tmp_path / "config.json"
        test_file.write_text('{"key": "value"}')
        result = read_json_file(str(test_file))
        assert result == {"key": "value"}

    def test_file_not_found(self):
        """Returns error for missing file."""
        # Before error handling: will raise FileNotFoundError
        # After error handling: should return error dict or raise handled exception
        with pytest.raises(FileNotFoundError):
            read_json_file("/nonexistent/path/file.json")

    def test_invalid_json(self, tmp_path):
        """Returns error for invalid JSON."""
        test_file = tmp_path / "invalid.json"
        test_file.write_text("not valid json {{{")
        # Before error handling: will raise json.JSONDecodeError
        with pytest.raises(json.JSONDecodeError):
            read_json_file(str(test_file))


class TestFetchJsonFromUrl:
    """Tests for fetch_json_from_url function."""

    def test_valid_url(self):
        """Successfully fetches JSON from URL."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"data": "test"}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = fetch_json_from_url("https://api.example.com/config")
            assert result == {"data": "test"}

    def test_timeout(self):
        """Returns error on timeout."""
        import urllib.error
        # Before error handling: will raise URLError
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
            with pytest.raises(urllib.error.URLError):
                fetch_json_from_url("https://api.example.com/config", timeout=1)

    def test_http_404(self):
        """Returns error for HTTP 404."""
        import urllib.error
        error = urllib.error.HTTPError(
            "https://api.example.com/config", 404, "Not Found", {}, None
        )
        # Before error handling: will raise HTTPError
        with patch("urllib.request.urlopen", side_effect=error):
            with pytest.raises(urllib.error.HTTPError):
                fetch_json_from_url("https://api.example.com/config")

    def test_invalid_json_response(self):
        """Returns error for non-JSON response."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"<html>Not JSON</html>"
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        # Before error handling: will raise JSONDecodeError
        with patch("urllib.request.urlopen", return_value=mock_response):
            with pytest.raises(json.JSONDecodeError):
                fetch_json_from_url("https://api.example.com/config")


class TestProcessConfig:
    """Tests for process_config function."""

    def test_valid_file(self, tmp_path):
        """Successfully processes valid file."""
        test_file = tmp_path / "config.json"
        test_file.write_text('{"setting": true}')
        result = process_config(str(test_file))
        assert result["success"] is True
        assert result["data"] == {"setting": True}
        assert result["error"] is None

    def test_valid_url(self):
        """Successfully processes valid URL."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"setting": true}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = process_config("https://api.example.com/config")
            assert result["success"] is True
            assert result["data"] == {"setting": True}

    def test_file_error_raises(self):
        """File errors raise exceptions (before error handling)."""
        # Before error handling: raises FileNotFoundError
        # After error handling: should return structured error dict
        with pytest.raises(FileNotFoundError):
            process_config("/nonexistent/file.json")

    def test_url_error_raises(self):
        """URL errors raise exceptions (before error handling)."""
        import urllib.error
        # Before error handling: raises URLError
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("fail")):
            with pytest.raises(urllib.error.URLError):
                process_config("https://api.example.com/config")


class TestBatchProcess:
    """Tests for batch_process function."""

    def test_all_valid(self, tmp_path):
        """Successfully processes all valid sources."""
        file1 = tmp_path / "config1.json"
        file2 = tmp_path / "config2.json"
        file1.write_text('{"id": 1}')
        file2.write_text('{"id": 2}')

        results = batch_process([str(file1), str(file2)])
        assert len(results) == 2
        assert all(r["success"] for r in results)

    def test_empty_list(self):
        """Handles empty source list."""
        results = batch_process([])
        assert results == []
