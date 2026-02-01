"""Unit tests for CLI submit command."""

import json
import pytest
from unittest.mock import patch, MagicMock

from cli.submit import generate_signature, submit_result


class TestSignature:
    """Test HMAC signature generation."""

    def test_generate_signature_deterministic(self):
        """Same payload always produces same signature."""
        payload = {"score": 83.6, "grade": "A"}
        sig1 = generate_signature(payload)
        sig2 = generate_signature(payload)
        assert sig1 == sig2

    def test_generate_signature_length(self):
        """Signature is 64 hex characters."""
        payload = {"score": 83.6}
        sig = generate_signature(payload)
        assert len(sig) == 64
        assert all(c in "0123456789abcdef" for c in sig)

    def test_signature_changes_with_payload(self):
        """Different payloads produce different signatures."""
        sig1 = generate_signature({"score": 83.6})
        sig2 = generate_signature({"score": 83.7})
        assert sig1 != sig2

    def test_signature_order_independent(self):
        """Key order doesn't affect signature (canonical JSON)."""
        sig1 = generate_signature({"a": 1, "b": 2})
        sig2 = generate_signature({"b": 2, "a": 1})
        assert sig1 == sig2


class TestSubmit:
    """Test submission flow."""

    @pytest.fixture
    def sample_result(self, tmp_path):
        """Create a sample result.json file."""
        result = {
            "headline_score": 83.6,
            "grade": "A",
            "suite_id": "refactor-storm",
            "suite_version": "1.0",
            "config_fingerprint": "a1b2c3d4e5f6",
            "config_sources": ["CLAUDE.md"],
            "behavior_scores": [
                {"behavior_id": "O-1.11", "score": 92.0, "grade": "S"}
            ],
        }
        path = tmp_path / "result.json"
        path.write_text(json.dumps(result))
        return str(path)

    def test_dry_run_no_submit(self, sample_result):
        """Dry run shows payload but doesn't submit."""
        result = submit_result(sample_result, dry_run=True)
        assert result["status"] == "dry_run"
        assert "payload" in result

    @patch("cli.submit.httpx.post")
    def test_successful_submit(self, mock_post, sample_result):
        """Successful submit returns share URL and percentile."""
        mock_post.return_value = MagicMock(
            status_code=201,
            json=lambda: {
                "submission_id": "abc12345-6789-0def-ghij-klmnopqrstuv",
                "share_url": "https://janus-labs.dev/result/abc12345",
                "percentile": 15.2,
                "rank": 5,
            },
        )

        result = submit_result(sample_result)

        assert result["status"] == "success"
        assert "share_url" in result
        assert result["score"] == 83.6
        # Verify we called FastAPI backend, not Supabase directly
        mock_post.assert_called_once()
        call_url = mock_post.call_args[0][0]
        assert "/api/submit" in call_url

    @patch("cli.submit.httpx.post")
    def test_rate_limit_exceeded(self, mock_post, sample_result):
        """Rate limit returns 429 error."""
        mock_post.return_value = MagicMock(
            status_code=429, json=lambda: {"detail": "Rate limit exceeded"}
        )

        with pytest.raises(RuntimeError, match="Rate limit exceeded"):
            submit_result(sample_result)

    @patch("cli.submit.httpx.post")
    def test_validation_error(self, mock_post, sample_result):
        """Invalid payload returns 400 error with signature mismatch."""
        mock_post.return_value = MagicMock(
            status_code=400, json=lambda: {"detail": "Invalid signature"}
        )

        with pytest.raises(RuntimeError, match="SUBMIT FAILED.*signature"):
            submit_result(sample_result)
