"""Output formatting utilities for verification results."""
import json
import sys
from pathlib import Path
from typing import Any

from .document import normalize_path_string


def write_batch_json_output(
    output_path: Path,
    results: list[dict[str, Any]],
    combined_time_info: dict[str, Any] | None,
    all_verified: bool,
    batch_mode: bool = False,
) -> None:
    """
    Write verification results to JSON file (consistent format for single and batch modes).

    Parameters
    ----------
    output_path : Path
        Path to output JSON file
    results : list[dict[str, Any]]
        List of results from each processed file
    combined_time_info : dict[str, Any] | None
        Combined time information across all files
    all_verified : bool
        Whether all files passed verification
    batch_mode : bool
        Whether this is batch mode (multiple files)

    Raises
    ------
    Exception
        If file writing fails
    """
    # Convert results to JSON-serializable format
    files_data = []
    for r in results:
        file_result = {
            "jsonl_file": normalize_path_string(str(r["jsonl_file"])),
            "document": r["target_document"],
            "verified": r["verified"],
            "time_info": r["time_info"],
            "suspicious_events": r["suspicious_events"],
            "template_diff": r.get("template_diff", ""),
            "reconstructed_code": r["reconstructed"],
        }

        # Add submitted_comparison if present
        if r.get("submitted_comparison") is not None:
            file_result["submitted_comparison"] = r["submitted_comparison"]

        files_data.append(file_result)

    # Use consistent format for both single and batch modes
    output_data = {
        "batch_mode": batch_mode,
        "total_files": len(results),
        "verified_count": sum(1 for r in results if r["verified"]),
        "all_verified": all_verified,
    }

    # Only include combined_time_info if present
    if combined_time_info is not None:
        output_data["combined_time_info"] = combined_time_info

    output_data["files"] = files_data

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    if batch_mode:
        print(f"Batch results written to {output_path}", file=sys.stderr)
    else:
        print(f"Results written to {output_path}", file=sys.stderr)
