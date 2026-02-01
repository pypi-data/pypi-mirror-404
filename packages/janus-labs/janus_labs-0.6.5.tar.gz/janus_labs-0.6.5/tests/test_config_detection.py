"""Tests for config detection module."""

import os
from pathlib import Path
from unittest.mock import patch

from config.detection import (
    INSTRUCTION_PATTERNS,
    detect_config,
    detect_execution_context,
    ExecutionContext,
)


class TestConfigDetection:
    """Test suite for config detection."""

    def test_no_instruction_file_returns_default(self, tmp_path: Path) -> None:
        """Empty directory should return default config."""
        result = detect_config(tmp_path)
        assert result.config_source == "default"
        assert result.config_hash == ""
        assert result.config_files == []
        assert result.captured_at is not None

    def test_claude_md_detected_as_custom(self, tmp_path: Path) -> None:
        """CLAUDE.md should trigger custom detection."""
        (tmp_path / "CLAUDE.md").write_text("# Test instructions", encoding="utf-8")
        result = detect_config(tmp_path)
        assert result.config_source == "custom"
        assert len(result.config_hash) == 12
        assert result.config_files == ["CLAUDE.md"]

    def test_multiple_files_combined_hash(self, tmp_path: Path) -> None:
        """Multiple instruction files should all be detected and hashed together."""
        (tmp_path / "CLAUDE.md").write_text("Claude instructions", encoding="utf-8")
        (tmp_path / ".github").mkdir()
        (tmp_path / ".github/copilot-instructions.md").write_text(
            "Copilot instructions",
            encoding="utf-8",
        )

        result = detect_config(tmp_path)
        assert result.config_source == "custom"
        assert len(result.config_files) == 2
        assert ".github/copilot-instructions.md" in result.config_files
        assert "CLAUDE.md" in result.config_files

    def test_hash_changes_with_content(self, tmp_path: Path) -> None:
        """Hash should change when file content changes."""
        (tmp_path / "CLAUDE.md").write_text("Version 1", encoding="utf-8")
        result1 = detect_config(tmp_path)

        (tmp_path / "CLAUDE.md").write_text("Version 2", encoding="utf-8")
        result2 = detect_config(tmp_path)

        assert result1.config_hash != result2.config_hash

    def test_each_supported_file_detected(self, tmp_path: Path) -> None:
        """Each supported instruction file pattern should be detected."""
        for pattern in INSTRUCTION_PATTERNS:
            for existing in INSTRUCTION_PATTERNS:
                existing_path = tmp_path / existing
                if existing_path.exists():
                    existing_path.unlink()
                if existing_path.parent != tmp_path and existing_path.parent.exists():
                    existing_path.parent.rmdir()

            file_path = tmp_path / pattern
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(f"Test content for {pattern}", encoding="utf-8")

            result = detect_config(tmp_path)
            assert result.config_source == "custom", f"Failed for {pattern}"
            assert pattern in result.config_files, f"Failed for {pattern}"

    def test_files_sorted_alphabetically(self, tmp_path: Path) -> None:
        """Config files should be sorted for deterministic hashing."""
        (tmp_path / "GEMINI.md").write_text("Gemini", encoding="utf-8")
        (tmp_path / "AGENTS.md").write_text("Agents", encoding="utf-8")
        (tmp_path / "CLAUDE.md").write_text("Claude", encoding="utf-8")

        result = detect_config(tmp_path)
        assert result.config_files == ["AGENTS.md", "CLAUDE.md", "GEMINI.md"]


class TestExecutionContextDetection:
    """Test suite for execution context detection."""

    def test_explicit_overrides_take_precedence(self, tmp_path: Path) -> None:
        """Explicit agent/model overrides should skip detection."""
        result = detect_execution_context(
            workspace_path=tmp_path,
            agent_override="custom-agent",
            model_override="custom-model",
        )
        assert result.agent == "custom-agent"
        assert result.model == "custom-model"
        assert result.detected is False

    def test_claude_code_env_detection(self, tmp_path: Path) -> None:
        """CLAUDE_CODE_VERSION env var should detect claude-code agent."""
        with patch.dict(os.environ, {"CLAUDE_CODE_VERSION": "1.0.0"}, clear=False):
            result = detect_execution_context(workspace_path=tmp_path)
            assert result.agent == "claude-code"
            assert result.interface == "cli-native"
            assert result.detected is True

    def test_vscode_ide_detection(self, tmp_path: Path) -> None:
        """VSCODE_PID env var should detect VS Code IDE."""
        with patch.dict(os.environ, {"VSCODE_PID": "12345"}, clear=False):
            result = detect_execution_context(workspace_path=tmp_path)
            assert result.ide == "vscode"
            assert result.interface == "ide-extension"

    def test_copilot_detection_in_vscode(self, tmp_path: Path) -> None:
        """VS Code without other markers should default to github-copilot."""
        # Clear potential conflicting env vars
        env_patch = {"VSCODE_PID": "12345"}
        vars_to_remove = ["CLAUDE_CODE_VERSION", "CODEX_CLI_VERSION", "GEMINI_CLI"]
        with patch.dict(os.environ, env_patch, clear=False):
            for var in vars_to_remove:
                os.environ.pop(var, None)
            result = detect_execution_context(workspace_path=tmp_path)
            assert result.agent == "github-copilot"
            assert result.ide == "vscode"

    def test_config_file_fallback_claude(self, tmp_path: Path) -> None:
        """CLAUDE.md should trigger claude-code agent detection."""
        (tmp_path / "CLAUDE.md").write_text("# Instructions", encoding="utf-8")
        # Clear env vars that might interfere
        with patch.dict(os.environ, {}, clear=False):
            for var in ["CLAUDE_CODE_VERSION", "VSCODE_PID", "CODEX_CLI_VERSION", "GEMINI_CLI"]:
                os.environ.pop(var, None)
            result = detect_execution_context(workspace_path=tmp_path)
            assert result.agent == "claude-code"
            assert result.model == "opus-4.5"
            assert result.detected is True

    def test_config_file_fallback_copilot(self, tmp_path: Path) -> None:
        """copilot-instructions.md should trigger github-copilot detection."""
        (tmp_path / ".github").mkdir()
        (tmp_path / ".github/copilot-instructions.md").write_text("# Instructions", encoding="utf-8")
        with patch.dict(os.environ, {}, clear=False):
            for var in ["CLAUDE_CODE_VERSION", "VSCODE_PID", "CODEX_CLI_VERSION", "GEMINI_CLI"]:
                os.environ.pop(var, None)
            result = detect_execution_context(workspace_path=tmp_path)
            assert result.agent == "github-copilot"
            assert result.model == "gpt-5.2"

    def test_manual_fallback_no_detection(self, tmp_path: Path) -> None:
        """No config files or env vars should fall back to manual."""
        with patch.dict(os.environ, {}, clear=False):
            for var in ["CLAUDE_CODE_VERSION", "VSCODE_PID", "CODEX_CLI_VERSION", "GEMINI_CLI", "JETBRAINS_IDE", "CURSOR_TRACE"]:
                os.environ.pop(var, None)
            result = detect_execution_context(workspace_path=tmp_path)
            assert result.agent == "manual"
            assert result.model == "unknown"
            assert result.interface == "terminal"
            assert result.detected is True

    def test_execution_context_dataclass(self) -> None:
        """ExecutionContext dataclass should have all expected fields."""
        ctx = ExecutionContext(
            agent="test-agent",
            model="test-model",
            interface="cli-native",
            ide="vscode",
            detected=False,
        )
        assert ctx.agent == "test-agent"
        assert ctx.model == "test-model"
        assert ctx.interface == "cli-native"
        assert ctx.ide == "vscode"
        assert ctx.detected is False
