"""
Cronista integration helpers for ryxpress.

This module provides functions to detect and report on chronicle objects
from the cronista package (Python equivalent of R's chronicler).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

__all__ = ["rxp_check_chronicles", "has_cronista", "chronicle_state", "chronicle_status"]


def has_cronista() -> bool:
    """Check if cronista package is available."""
    try:
        import cronista  # noqa: F401
        return True
    except ImportError:
        return False


def _is_chronicle(obj: Any) -> bool:
    """Check if object is a Chronicle instance."""
    if not has_cronista():
        return False
    try:
        from cronista import Chronicle
        return isinstance(obj, Chronicle)
    except ImportError:
        return False


def chronicle_state(obj: Any) -> Optional[str]:
    """
    Determine chronicle status: "success", "warning", or "nothing".

    Args:
        obj: Object to check

    Returns:
        "success", "warning", "nothing", or None if not a chronicle
    """
    if not _is_chronicle(obj):
        return None

    # Check if value is Nothing (obj.is_ok() returns False)
    if not obj.is_ok():
        return "nothing"

    # Check log for NOK entries (warnings/errors that didn't cause Nothing)
    log_df = getattr(obj, "log_df", [])
    has_nok = any("NOK" in str(row.get("outcome", "")) for row in log_df)

    if has_nok:
        return "warning"

    return "success"


def chronicle_status(obj: Any) -> Optional[Dict[str, Any]]:
    """
    Get detailed chronicle status information.

    Args:
        obj: A chronicle object

    Returns:
        Dict with status information, or None if not a chronicle
    """
    if not _is_chronicle(obj):
        return None

    state = chronicle_state(obj)
    is_nothing = (state == "nothing")

    log_df = getattr(obj, "log_df", [])
    nok_ops = [row for row in log_df if "NOK" in str(row.get("outcome", ""))]

    return {
        "is_chronicle": True,
        "state": state,
        "is_nothing": is_nothing,
        "has_warnings": (state == "warning"),
        "num_operations": len(log_df),
        "num_failed": len(nok_ops),
        "failed_functions": [row.get("function", "<unknown>") for row in nok_ops],
        "messages": [row.get("message") for row in nok_ops if row.get("message")],
    }


def chronicle_symbol(state: str) -> str:
    """Get the display symbol for a chronicle state."""
    symbols = {
        "success": "\u2713",  # checkmark
        "warning": "\u26A0",  # warning sign
        "nothing": "\u2716",  # X mark
    }
    return symbols.get(state, "?")


def format_chronicle_message(derivation_name: str, status: Dict[str, Any]) -> str:
    """Format chronicle status message for display."""
    if status is None:
        return ""

    symbol = chronicle_symbol(status["state"])

    if status["state"] == "success":
        return f"{symbol} {derivation_name} (chronicle: OK)"

    msg = f"{symbol} {derivation_name} (chronicle: {status['state'].upper()})"

    if status["failed_functions"]:
        msg += f"\n    Failed: {', '.join(status['failed_functions'])}"

    if status["messages"]:
        real_msgs = [m for m in status["messages"] if m and m != "Short-circuited due to Nothing"]
        if real_msgs:
            msg += f"\n    Message: {'; '.join(real_msgs)}"

    return msg


def rxp_check_chronicles(
    project_path: str = ".",
    which_log: Optional[str] = None,
) -> Optional[List[Dict[str, Any]]]:
    """
    Check Pipeline Outputs for Chronicle Status.

    Scans all derivation outputs for chronicle objects and reports their status:
    success (Just, no warnings), warning (Just with warnings), or nothing
    (failed computation).

    Args:
        project_path: Path to the root directory of the project.
        which_log: If None, the most recent build log is used. If a string,
            it's used as a regex to match against available log files.

    Returns:
        A list of dicts with chronicle status info, or None if cronista
        is not installed or no chronicle objects are found.
    """
    if not has_cronista():
        print("cronista package not installed. Chronicle checking not available.")
        return None

    # Import here to avoid circular imports
    from .inspect_logs import rxp_inspect
    from .read_load import rxp_read

    try:
        build_log = rxp_inspect(project_path=project_path, which_log=which_log)
    except Exception as e:
        logger.debug("Failed to inspect build log: %s", e)
        return None

    if not isinstance(build_log, list):
        return None

    results = []

    for row in build_log:
        if not isinstance(row, dict):
            continue

        deriv_name = row.get("derivation") or row.get("deriv") or row.get("name")
        if not deriv_name or deriv_name == "all-derivations":
            continue

        # Check if build was successful
        build_success = row.get("build_success", True)
        if not build_success:
            continue

        # Try to read the derivation
        try:
            obj = rxp_read(deriv_name, which_log=which_log, project_path=project_path)
        except Exception:
            continue

        status = chronicle_status(obj)
        if status is None:
            continue  # Not a chronicle object

        results.append({
            "derivation": deriv_name,
            "chronicle_state": status["state"],
            "num_operations": status["num_operations"],
            "num_failed": status["num_failed"],
            "failed_functions": status["failed_functions"],
            "messages": status["messages"],
        })

    if not results:
        print("No chronicle objects found in pipeline outputs.")
        return None

    # Display summary with symbols
    print("Chronicle status:")
    for res in results:
        status = {
            "state": res["chronicle_state"],
            "failed_functions": res["failed_functions"],
            "messages": res["messages"],
        }
        print(format_chronicle_message(res["derivation"], status))

    # Summary counts
    n_success = sum(1 for r in results if r["chronicle_state"] == "success")
    n_warning = sum(1 for r in results if r["chronicle_state"] == "warning")
    n_nothing = sum(1 for r in results if r["chronicle_state"] == "nothing")

    print(f"\nSummary: {n_success} success, {n_warning} with warnings, {n_nothing} nothing")

    if n_nothing > 0:
        import warnings
        warnings.warn(f"{n_nothing} derivation(s) contain Nothing values!")

    return results
