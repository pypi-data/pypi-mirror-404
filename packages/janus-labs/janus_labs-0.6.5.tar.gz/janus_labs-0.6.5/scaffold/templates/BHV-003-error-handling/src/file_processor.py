"""File processor module - needs comprehensive error handling."""

import json
import urllib.request
from pathlib import Path


def read_json_file(file_path: str) -> dict:
    """
    Read and parse a JSON file.

    NEEDS ERROR HANDLING FOR:
    - File not found
    - Permission denied
    - Invalid JSON format

    Args:
        file_path: Path to the JSON file

    Returns:
        Parsed JSON as dictionary
    """
    with open(file_path, "r") as f:
        return json.load(f)


def fetch_json_from_url(url: str, timeout: int = 10) -> dict:
    """
    Fetch JSON data from a URL.

    NEEDS ERROR HANDLING FOR:
    - Network timeout
    - Connection error
    - Invalid JSON response
    - HTTP errors (404, 500, etc.)

    Args:
        url: URL to fetch JSON from
        timeout: Request timeout in seconds

    Returns:
        Parsed JSON as dictionary
    """
    with urllib.request.urlopen(url, timeout=timeout) as response:
        data = response.read().decode("utf-8")
        return json.loads(data)


def process_config(source: str) -> dict:
    """
    Process configuration from file or URL.

    NEEDS ERROR HANDLING FOR:
    - All errors from read_json_file
    - All errors from fetch_json_from_url
    - Invalid source format

    Args:
        source: File path or URL to configuration

    Returns:
        dict with keys:
            - success: bool
            - data: parsed config or None
            - error: error message or None
            - error_code: string error code or None
    """
    if source.startswith(("http://", "https://")):
        data = fetch_json_from_url(source)
    else:
        data = read_json_file(source)

    return {
        "success": True,
        "data": data,
        "error": None,
        "error_code": None,
    }


def batch_process(sources: list[str]) -> list[dict]:
    """
    Process multiple configuration sources.

    NEEDS ERROR HANDLING FOR:
    - Individual source failures (should not stop batch)
    - Empty sources list
    - Invalid source types

    Args:
        sources: List of file paths or URLs

    Returns:
        List of process_config results
    """
    results = []
    for source in sources:
        result = process_config(source)
        results.append(result)
    return results
