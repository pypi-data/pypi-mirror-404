"""Config detection module for identifying agent instruction files and execution context."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, UTC
import hashlib
import os
from pathlib import Path
from typing import List, Optional


@dataclass
class ExecutionContext:
    """Execution context describing how the benchmark was run.

    This captures what agent/tool is running the benchmark and how,
    enabling leaderboard segmentation by agent type.
    """

    agent: str  # "claude-code", "github-copilot", "gemini-cli", "codex", "manual"
    model: str  # "opus-4.5", "gpt-5.2", "gemini-3-pro", etc.
    interface: str  # "ide-extension", "cli-native", "terminal"
    ide: Optional[str]  # "vscode", "jetbrains", "cursor", None
    detected: bool  # True if auto-detected, False if explicitly specified


def detect_execution_context(
    workspace_path: Optional[Path] = None,
    agent_override: Optional[str] = None,
    model_override: Optional[str] = None,
) -> ExecutionContext:
    """
    Auto-detect execution context from environment and config files.

    Detection priority:
    1. Explicit overrides (--agent, --model flags)
    2. Environment variables (CLAUDE_CODE_VERSION, VSCODE_PID, etc.)
    3. Config files present (CLAUDE.md, copilot-instructions.md, etc.)
    4. Fallback to "manual" + "unknown"

    Args:
        workspace_path: Path to check for config files
        agent_override: Explicit agent name (skips detection)
        model_override: Explicit model name (skips detection)

    Returns:
        ExecutionContext with detected or specified values
    """
    agent = agent_override
    model = model_override
    interface = "terminal"
    ide = None
    detected = False

    # Detect IDE from environment
    if os.environ.get("VSCODE_PID") or os.environ.get("VSCODE_CLI"):
        ide = "vscode"
        interface = "ide-extension"
    elif os.environ.get("JETBRAINS_IDE"):
        ide = "jetbrains"
        interface = "ide-extension"
    elif os.environ.get("CURSOR_TRACE"):
        ide = "cursor"
        interface = "ide-extension"

    # Detect agent from environment
    if not agent:
        detected = True

        # Check for known agent environment markers
        if os.environ.get("CLAUDE_CODE_VERSION"):
            agent = "claude-code"
            interface = "cli-native"
            model = model or os.environ.get("ANTHROPIC_MODEL", "opus-4.5")
        elif os.environ.get("CODEX_CLI_VERSION"):
            agent = "codex"
            interface = "cli-native"
            model = model or "gpt-5.2"
        elif os.environ.get("GEMINI_CLI"):
            agent = "gemini-cli"
            interface = "cli-native"
            model = model or "gemini-3-pro"
        elif ide == "vscode":
            # VS Code with Copilot is most common
            agent = "github-copilot"
            model = model or "gpt-5.2"
        else:
            # Fall back to config file detection
            if workspace_path:
                config_files = []
                for pattern in INSTRUCTION_PATTERNS:
                    if (workspace_path / pattern).exists():
                        config_files.append(pattern)

                if "CLAUDE.md" in config_files:
                    agent = "claude-code"
                    model = model or "opus-4.5"
                elif ".github/copilot-instructions.md" in config_files:
                    agent = "github-copilot"
                    model = model or "gpt-5.2"
                elif "AGENTS.md" in config_files or "codex.md" in config_files:
                    agent = "codex"
                    model = model or "gpt-5.2"
                elif "GEMINI.md" in config_files:
                    agent = "gemini-cli"
                    model = model or "gemini-3-pro"

            # Final fallback
            if not agent:
                agent = "manual"
                model = model or "unknown"

    return ExecutionContext(
        agent=agent or "manual",
        model=model or "unknown",
        interface=interface,
        ide=ide,
        detected=detected,
    )


@dataclass
class ConfigMetadata:
    """Metadata about detected configuration files."""

    config_source: str  # "default" or "custom"
    config_hash: str  # SHA-256 truncated to 12 chars
    config_files: List[str]  # List of detected files
    captured_at: str  # ISO timestamp


INSTRUCTION_PATTERNS = [
    "CLAUDE.md",  # Claude Code
    ".github/copilot-instructions.md",  # GitHub Copilot
    "AGENTS.md",  # Codex CLI
    "codex.md",  # Codex CLI alt
    "GEMINI.md",  # Gemini CLI
]


def detect_config(workspace_path: Path) -> ConfigMetadata:
    """
    Detect instruction files in the workspace.

    Args:
        workspace_path: Root path to search for instruction files

    Returns:
        ConfigMetadata with detection results
    """
    detected_files: List[str] = []

    for pattern in INSTRUCTION_PATTERNS:
        file_path = workspace_path / pattern
        if file_path.exists():
            detected_files.append(pattern)

    detected_files.sort()
    captured_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")

    if not detected_files:
        return ConfigMetadata(
            config_source="default",
            config_hash="",
            config_files=[],
            captured_at=captured_at,
        )

    combined_content = ""
    for file_name in detected_files:
        file_path = workspace_path / file_name
        combined_content += file_path.read_text(encoding="utf-8")

    full_hash = hashlib.sha256(combined_content.encode("utf-8")).hexdigest()
    truncated_hash = full_hash[:12]

    return ConfigMetadata(
        config_source="custom",
        config_hash=truncated_hash,
        config_files=detected_files,
        captured_at=captured_at,
    )
