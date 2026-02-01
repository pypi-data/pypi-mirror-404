"""Cross-platform clipboard utilities for Janus Labs CLI."""

import platform
import subprocess


def copy_to_clipboard(text: str) -> bool:
    """
    Copy text to system clipboard (cross-platform).

    Supports:
    - Windows: clip command
    - macOS: pbcopy command
    - Linux: xclip (must be installed)

    Args:
        text: Text to copy to clipboard

    Returns:
        True if successful, False otherwise
    """
    system = platform.system()

    try:
        if system == "Windows":
            # Windows clip command
            process = subprocess.run(
                ["clip"],
                input=text.encode("utf-16-le"),  # Windows clipboard uses UTF-16
                check=True,
                capture_output=True,
            )
            return process.returncode == 0

        if system == "Darwin":
            # macOS pbcopy command
            process = subprocess.run(
                ["pbcopy"],
                input=text.encode("utf-8"),
                check=True,
                capture_output=True,
            )
            return process.returncode == 0

        # Linux - try xclip first, then xsel
        try:
            process = subprocess.run(
                ["xclip", "-selection", "clipboard"],
                input=text.encode("utf-8"),
                check=True,
                capture_output=True,
            )
            return process.returncode == 0
        except FileNotFoundError:
            # Try xsel as fallback
            try:
                process = subprocess.run(
                    ["xsel", "--clipboard", "--input"],
                    input=text.encode("utf-8"),
                    check=True,
                    capture_output=True,
                )
                return process.returncode == 0
            except FileNotFoundError:
                return False

    except (FileNotFoundError, subprocess.CalledProcessError, OSError):
        return False


def is_clipboard_available() -> bool:
    """
    Check if clipboard operations are available on this system.

    Returns:
        True if clipboard can be used, False otherwise
    """
    system = platform.system()

    try:
        if system == "Windows":
            # clip is always available on Windows
            return True

        if system == "Darwin":
            # pbcopy is always available on macOS
            return True

        # Linux - check for xclip or xsel
        try:
            subprocess.run(
                ["xclip", "-version"],
                capture_output=True,
                check=False,
            )
            return True
        except FileNotFoundError:
            pass

        try:
            subprocess.run(
                ["xsel", "--version"],
                capture_output=True,
                check=False,
            )
            return True
        except FileNotFoundError:
            pass

        return False

    except (subprocess.SubprocessError, OSError):
        return False
