#!/usr/bin/env python3
"""
CLI Submit Command - Posts benchmark results to FastAPI backend.

SECURITY: CLI does NOT have Supabase credentials. It POSTs to the
FastAPI backend which handles validation, rate limiting, and DB insert.

Usage:
    python -m cli submit result.json
    python -m cli submit result.json --dry-run
    python -m cli submit result.json --github myhandle
"""

import hashlib
import hmac
import json
import os
import sys
from datetime import datetime, timezone
from typing import Optional, List

import httpx

# Backend URL (no Supabase credentials needed!)
API_URL = os.environ.get("JANUS_LABS_API", "https://fulfilling-courtesy-production-9c2c.up.railway.app")
MAX_BUNDLE_BYTES = 100 * 1024

# Public community key - zero friction for public leaderboard
# Anti-cheat is handled via workspace_hash validation, not authentication
PUBLIC_COMMUNITY_KEY = "janus-labs-public-v1"
_HMAC_SECRET = os.environ.get("JANUS_HMAC_SECRET", PUBLIC_COMMUNITY_KEY)

# For backwards compatibility
HMAC_SECRET = _HMAC_SECRET


def generate_signature(payload: dict, secret: str = None) -> str:
    """Generate HMAC-SHA256 signature for payload."""
    if secret is None:
        secret = _HMAC_SECRET
    # Canonical JSON (sorted keys, no spaces)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    sig = hmac.new(
        secret.encode(), canonical.encode(), hashlib.sha256
    ).hexdigest()[:64]
    return sig


def _score_to_grade(score: float) -> str:
    """Convert numeric score to letter grade.

    Backend expects single letters: S, A, B, C, D, F
    S = 95+, A = 85+, B = 70+, C = 55+, D = 40+, F = below
    """
    if score >= 95:
        return "S"
    elif score >= 85:
        return "A"
    elif score >= 70:
        return "B"
    elif score >= 55:
        return "C"
    elif score >= 40:
        return "D"
    else:
        return "F"


def _behavior_id_to_code(behavior_id: str) -> str:
    """Convert behavior ID to backend format.

    Backend expects: ^[A-Z]-\\d+\\.\\d+$ (e.g., "B-1.0")
    Input: "BHV-001-test-cheating" -> "B-1.0"
    """
    import re
    # Extract number from behavior ID
    match = re.search(r"(\d+)", behavior_id)
    if match:
        num = int(match.group(1))
        return f"B-{num}.0"
    return "B-1.0"


def _extract_bundle(result: dict, result_file: str) -> Optional[dict]:
    """Extract judge bundle from result or load from bundle file."""
    from pathlib import Path

    # Check for associated bundle file (result.bundle.json)
    bundle_path = Path(result_file).with_suffix(".bundle.json")
    if bundle_path.exists():
        with bundle_path.open() as f:
            bundle = json.load(f)
        rollouts: List[dict] = [{
            "prompt": bundle.get("task", ""),
            "response": bundle.get("output", ""),
            "repo_diff": bundle.get("code_diff", ""),
            "test_output": bundle.get("test_output", ""),
        }]
        return {
            "behavior_id": result.get("behavior_id", "B-1"),
            "config_fingerprint": result.get("config_hash", "")[:12] or "default12345",
            "rollouts": rollouts,
            "behavior_name": result.get("behavior_name"),
            "behavior_description": result.get("behavior_description"),
        }

    # Extract from git_diff in result
    git_diff = result.get("git_diff", {})
    if git_diff.get("patch"):
        rollouts: List[dict] = [{
            "prompt": f"Task: {result.get('behavior_id', 'unknown')}",
            "response": "Agent completed the task",
            "repo_diff": git_diff.get("patch", "")[:2000],
            "test_output": str(result.get("test_results", {}).get("output", ""))[:500],
        }]
        return {
            "behavior_id": result.get("behavior_id", "B-1"),
            "config_fingerprint": result.get("config_hash", "")[:12] or "default12345",
            "rollouts": rollouts,
        }

    return None


def _truncate_bundle(bundle: Optional[dict], max_bytes: int = MAX_BUNDLE_BYTES) -> Optional[dict]:
    """Trim bundle fields to stay within backend size limits."""
    if not bundle:
        return None

    def _size(value: dict) -> int:
        return len(json.dumps(value, separators=(",", ":"), ensure_ascii=True).encode("utf-8"))

    if _size(bundle) <= max_bytes:
        return bundle

    truncated = json.loads(json.dumps(bundle))
    rollouts = truncated.get("rollouts", [])
    if len(rollouts) > 1:
        truncated["rollouts"] = rollouts[:1]

    fields = ("repo_diff", "test_output", "response", "prompt")
    for _ in range(6):
        if _size(truncated) <= max_bytes:
            return truncated
        for rollout in truncated.get("rollouts", []):
            for field in fields:
                value = rollout.get(field)
                if isinstance(value, str) and value:
                    new_len = max(200, int(len(value) * 0.5))
                    if len(value) > new_len:
                        rollout[field] = value[:new_len]

    if _size(truncated) <= max_bytes:
        return truncated

    for rollout in truncated.get("rollouts", []):
        for field in ("repo_diff", "test_output"):
            if field in rollout:
                rollout[field] = ""
        for field in ("response", "prompt"):
            value = rollout.get(field)
            if isinstance(value, str):
                rollout[field] = value[:200]

    if _size(truncated) <= max_bytes:
        return truncated

    return None


def submit_result(
    result_file: str,
    github_handle: Optional[str] = None,
    dry_run: bool = False,
    no_judge: bool = False,
) -> dict:
    """Submit benchmark result to FastAPI backend.

    Handles both suite-level results (from janus run) and single-behavior
    results (from janus score).
    """

    with open(result_file) as f:
        result = json.load(f)

    # Extract bundle for backend judging (JL-174.4)
    bundle_data = None
    if not no_judge:
        bundle_data = _extract_bundle(result, result_file)
        if bundle_data:
            truncated_bundle = _truncate_bundle(bundle_data)
            if truncated_bundle is None:
                print(f"Warning: bundle exceeds {MAX_BUNDLE_BYTES // 1024}KB; skipping backend judging.")
            elif truncated_bundle is not bundle_data:
                print("Note: bundle truncated to fit size limits.")
            bundle_data = truncated_bundle

    # Detect result type and normalize to suite format
    if "headline_score" in result:
        # Suite-level result from janus run
        score = result["headline_score"]
        grade = result["grade"]
        suite_id = result["suite_id"]
        behaviors = [
            {
                "code": _behavior_id_to_code(b["behavior_id"]),
                "score": b["score"],
                "grade": b["grade"],
            }
            for b in result.get("behavior_scores", [])
        ]
    elif "behavior_id" in result:
        # Single behavior result from janus score
        # Convert 1-10 score to 0-100 for consistency
        raw_score = result.get("outcome_score") or result.get("score")
        score = raw_score * 10  # 9.0 -> 90
        grade = _score_to_grade(score)
        # Extract suite from behavior ID (e.g., BHV-001-test-cheating -> derive from context)
        suite_id = result.get("suite_id", "refactor-storm")
        behavior_code = _behavior_id_to_code(result["behavior_id"])
        behaviors = [
            {"code": behavior_code, "score": score, "grade": grade}
        ]
    else:
        raise RuntimeError(
            "SUBMIT FAILED: Unrecognized result format\n"
            "\n"
            "  Detail: result.json is missing headline_score or behavior_id.\n"
            "\n"
            "  Try: Re-run 'janus-labs score -o result.json' to generate a fresh result\n"
        )

    # Generate config hash (8-12 chars required by backend)
    config_fp = result.get("config_fingerprint", "")
    if not config_fp or config_fp == "unknown" or len(config_fp) < 8:
        # Generate hash from result content
        config_fp = hashlib.sha256(
            json.dumps(result, sort_keys=True).encode()
        ).hexdigest()[:12]
    elif len(config_fp) > 12:
        # Truncate if too long (backend max is 12)
        config_fp = config_fp[:12]

    # Build submission payload
    payload = {
        "score": score,
        "grade": grade,
        "agent": result.get("agent", "claude-code"),
        "model": result.get("model", "opus-4.5"),
        "suite": suite_id,
        "suite_version": result.get("suite_version", "1.0"),
        "cli_version": result.get("cli_version", "0.6.4"),
        "config_hash": config_fp,
        "config_sources": result.get("config_sources", ["CLAUDE.md"]),
        "config_badge": result.get("config_badge", "default"),
        "behaviors": behaviors,
        "client_timestamp": datetime.now(timezone.utc).isoformat(),
        "workspace_hash": result.get("workspace_hash"),  # Anti-cheat validation
    }

    # Include execution context if available (JL-162)
    exec_ctx = result.get("execution_context")
    if exec_ctx:
        payload["execution_context"] = {
            "interface": exec_ctx.get("interface", "terminal"),
            "ide": exec_ctx.get("ide"),
            "detected": exec_ctx.get("detected", True),
        }

    if github_handle:
        payload["github_handle"] = github_handle

    # Add bundle for backend judging (JL-174.4)
    if bundle_data:
        payload["bundle"] = bundle_data

    # Generate signature (uses public community key by default)
    payload["signature"] = generate_signature(payload)

    if dry_run:
        print("DRY RUN - Would submit:")
        print(json.dumps(payload, indent=2))
        return {"status": "dry_run", "payload": payload}

    # Submit to FastAPI backend (NOT directly to Supabase)
    try:
        response = httpx.post(
            f"{API_URL}/api/submit",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30.0,
        )
    except httpx.ConnectError as e:
        raise RuntimeError(
            "SUBMIT FAILED: Connection error\n"
            "\n"
            f"  Detail: Could not reach {API_URL}\n"
            f"  Error: {e}\n"
            "\n"
            "  Try: Check your internet connection and re-run the submit.\n"
        )
    except httpx.TimeoutException:
        raise RuntimeError(
            "SUBMIT FAILED: Request timed out\n"
            "\n"
            "  Detail: The server did not respond within 30 seconds.\n"
            "\n"
            "  Try: Wait a moment and submit again.\n"
        )

    if response.status_code == 201:
        data = response.json()

        # Display judge result if available (JL-174.4)
        judge = data.get("judge")

        print(f"\n{'='*50}")
        print("  SUBMITTED SUCCESSFULLY!")
        print(f"{'='*50}")

        if judge:
            print(f"\n  Score: {judge['score']:.1f} (Grade {judge['grade']})")
            print(f"  Reason: {judge['reason']}")
            print(f"  Model: {judge['model_used']}")
            if judge.get('cached'):
                print("  (cached result)")
        else:
            print(f"  Score: {payload['score']} (Grade {payload['grade']})")

        print(f"\n  Rank: #{data.get('rank', '?')} on {payload['suite']}")
        print(f"  Percentile: Top {data.get('percentile', '?')}%")
        print(f"  Share: {data['share_url']}")
        print(f"{'='*50}\n")

        return {
            "status": "success",
            "submission_id": data["submission_id"],
            "share_url": data["share_url"],
            "percentile": data.get("percentile"),
            "rank": data.get("rank"),
            "score": judge["score"] if judge else payload["score"],
            "judge": judge,
        }
    elif response.status_code == 429:
        raise RuntimeError(
            "SUBMIT FAILED: Rate limit exceeded\n"
            "\n"
            "  Detail: You can only submit once per minute.\n"
            "\n"
            "  Try: Wait 60 seconds and submit again.\n"
        )
    elif response.status_code in (401, 403):
        detail = response.json().get("detail", "Invalid signature")
        error_msg = (
            f"SUBMIT FAILED: Signature validation error\n"
            f"\n"
            f"  Detail: {detail}\n"
            f"\n"
            f"  This usually means the result.json was modified after scoring.\n"
            f"  The signature is computed at score time and any changes invalidate it.\n"
        )
        if _HMAC_SECRET != PUBLIC_COMMUNITY_KEY:
            error_msg += (
                f"\n"
                f"  You have a custom JANUS_HMAC_SECRET set. Try unsetting it:\n"
                f"    unset JANUS_HMAC_SECRET\n"
                f"\n"
            )
        error_msg += (
            f"  Try: Re-run 'janus-labs score -o result.json' to generate a fresh result\n"
            f"       Then: janus-labs submit result.json --github <handle>\n"
        )
        raise RuntimeError(error_msg)
    elif response.status_code == 400:
        detail = response.json().get("detail", response.text)

        # Check for specific known issues
        if "signature" in str(detail).lower():
            raise RuntimeError(
                f"SUBMIT FAILED: Payload signature mismatch\n"
                f"\n"
                f"  Detail: {detail}\n"
                f"\n"
                f"  The result.json was modified after scoring, invalidating the signature.\n"
                f"  Common causes:\n"
                f"    - Editing the JSON file manually\n"
                f"    - Running a script that modifies values (e.g., rounding)\n"
                f"    - Copying/moving the file incorrectly\n"
                f"\n"
                f"  Try: Re-run 'janus-labs score -o result.json' in your workspace\n"
                f"       Then submit the fresh result without modification.\n"
            )
        elif "workspace_hash" in str(detail).lower():
            raise RuntimeError(
                f"SUBMIT FAILED: Workspace hash validation failed\n"
                f"\n"
                f"  Detail: {detail}\n"
                f"\n"
                f"  The workspace state doesn't match the scored result.\n"
                f"\n"
                f"  Try: cd into your janus-task workspace and re-run:\n"
                f"       janus-labs score -o result.json\n"
                f"       janus-labs submit result.json --github <handle>\n"
            )
        else:
            raise RuntimeError(
                f"SUBMIT FAILED: Validation error\n"
                f"\n"
                f"  Detail: {detail}\n"
                f"\n"
                f"  The result.json format may be incorrect.\n"
                f"\n"
                f"  Try: janus-labs submit result.json --dry-run\n"
                f"       to inspect the payload being submitted.\n"
                f"\n"
                f"  If the issue persists, re-run:\n"
                f"       janus-labs score -o result.json\n"
            )
    elif response.status_code == 422:
        detail = response.json().get("detail", response.text)
        raise RuntimeError(
            f"SUBMIT FAILED: Schema validation error\n"
            f"\n"
            f"  Detail: {detail}\n"
            f"\n"
            f"  The result.json fields don't match the expected format.\n"
            f"\n"
            f"  Try: pip install --upgrade janus-labs\n"
            f"       Then re-run: janus-labs score -o result.json\n"
            f"\n"
            f"  If using an older result file, regenerate it with the latest CLI.\n"
        )
    else:
        raise RuntimeError(
            f"SUBMIT FAILED: HTTP {response.status_code}\n"
            f"\n"
            f"  Response: {response.text[:200]}\n"
            f"\n"
            f"  Try: Check your internet connection and try again.\n"
            f"       If the issue persists, report at:\n"
            f"       https://github.com/alexanderaperry-arch/janus-labs/issues\n"
        )


def cmd_submit(args) -> int:
    """Handle submit subcommand."""
    try:
        result = submit_result(
            args.result_file,
            args.github,
            args.dry_run,
            getattr(args, 'no_judge', False),
        )
        return 0
    except FileNotFoundError:
        print(
            "SUBMIT FAILED: Result file not found\n"
            "\n"
            f"  Detail: {args.result_file}\n"
            "\n"
            "  Try: Check the path and re-run:\n"
            "       janus-labs submit result.json --github <handle>\n",
            file=sys.stderr,
        )
        return 1
    except json.JSONDecodeError as e:
        print(
            "SUBMIT FAILED: Invalid JSON in result file\n"
            "\n"
            f"  Detail: {e}\n"
            "\n"
            "  Try: Re-run 'janus-labs score -o result.json' to regenerate it\n"
            "       or fix the JSON before submitting.\n",
            file=sys.stderr,
        )
        return 1
    except RuntimeError as e:
        print(f"{e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(
            "SUBMIT FAILED: Unexpected error\n"
            "\n"
            f"  Detail: {e}\n"
            "\n"
            "  Try: Re-run the command or use --dry-run to inspect the payload.\n",
            file=sys.stderr,
        )
        return 1
