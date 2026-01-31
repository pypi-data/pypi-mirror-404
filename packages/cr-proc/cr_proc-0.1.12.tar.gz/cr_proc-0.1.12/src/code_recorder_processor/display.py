"""Display utilities for CLI output."""
import sys
from datetime import datetime
from typing import Any


def display_time_info(time_info: dict[str, Any] | None, is_combined: bool = False) -> None:
    """
    Display elapsed time and time limit information.

    Parameters
    ----------
    time_info : dict[str, Any] | None
        Time information from check_time_limit, or None if no time data
    is_combined : bool
        Whether this is combined time info from multiple files
    """
    if not time_info:
        return

    if is_combined:
        file_count = time_info.get("file_count", 1)
        print(f"\nCOMBINED TIME REPORT ({file_count} recordings):", file=sys.stderr)
        print(f"Total elapsed editing time: {time_info['minutes_elapsed']} minutes", file=sys.stderr)
        print(f"Overall time span: {time_info['overall_span_minutes']:.2f} minutes", file=sys.stderr)
    else:
        print(
            f"Elapsed editing time: {time_info['minutes_elapsed']} minutes",
            file=sys.stderr,
        )

        first_ts = datetime.fromisoformat(
            time_info["first_timestamp"].replace("Z", "+00:00")
        )
        last_ts = datetime.fromisoformat(
            time_info["last_timestamp"].replace("Z", "+00:00")
        )
        time_span = (last_ts - first_ts).total_seconds() / 60

        print(f"Time span (first to last edit): {time_span:.2f} minutes", file=sys.stderr)

    if time_info["exceeds_limit"]:
        print("\nTime limit exceeded!", file=sys.stderr)
        print(f"  Limit: {time_info['time_limit_minutes']} minutes", file=sys.stderr)
        if not is_combined:
            print(f"  First edit: {time_info['first_timestamp']}", file=sys.stderr)
            print(f"  Last edit: {time_info['last_timestamp']}", file=sys.stderr)


def display_suspicious_event(event: dict[str, Any], show_details: bool) -> None:
    """
    Display a single suspicious event.

    Parameters
    ----------
    event : dict[str, Any]
        Suspicious event data
    show_details : bool
        Whether to show detailed autocomplete events
    """
    reason = event.get("reason", "unknown")

    # Handle aggregate auto-complete events
    if event.get("event_index") == -1 and "detailed_events" in event:
        event_count = event["event_count"]
        total_chars = event["total_chars"]
        print(
            f"  Aggregate: {event_count} auto-complete/small paste events "
            f"({total_chars} total chars)",
            file=sys.stderr,
        )

        if show_details:
            print("    Detailed events:", file=sys.stderr)
            for detail in event["detailed_events"]:
                detail_idx = detail["event_index"]
                detail_lines = detail["line_count"]
                detail_chars = detail["char_count"]
                detail_frag = detail["newFragment"]
                print(
                    f"      Event #{detail_idx}: {detail_lines} lines, "
                    f"{detail_chars} chars",
                    file=sys.stderr,
                )
                print("        ```", file=sys.stderr)
                for line in detail_frag.split("\n"):
                    print(f"        {line}", file=sys.stderr)
                print("        ```", file=sys.stderr)

    elif "event_indices" in event and reason == "rapid one-line pastes (AI indicator)":
        # Rapid paste sequences (AI indicator) - show aggregate style
        indices = event["event_indices"]
        print(
            f"  AI Rapid Paste: Events #{indices[0]}-#{indices[-1]} "
            f"({event['line_count']} lines, {event['char_count']} chars, "
            f"{len(indices)} events in < 1 second)",
            file=sys.stderr,
        )

        if show_details and "detailed_events" in event:
            # Combine all detailed events into one block
            combined_content = "".join(
                detail["newFragment"] for detail in event["detailed_events"]
            )
            print("    Combined output:", file=sys.stderr)
            print("        ```", file=sys.stderr)
            for line in combined_content.split("\n"):
                print(f"        {line}", file=sys.stderr)
            print("        ```", file=sys.stderr)

    elif "event_indices" in event:
        # Other multi-event clusters
        indices = event.get("event_indices", [event["event_index"]])
        print(
            f"  Events #{indices[0]}-#{indices[-1]} ({reason}): "
            f"{event['line_count']} lines, {event['char_count']} chars",
            file=sys.stderr,
        )

    else:
        new_fragment = event["newFragment"].replace("\n", "\n    ")
        print(
            f"  Event #{event['event_index']} ({reason}): "
            f"{event['line_count']} lines, {event['char_count']} chars - "
            f"newFragment:\n    ```\n    {new_fragment}\n    ```",
            file=sys.stderr,
        )


def display_suspicious_events(
    suspicious_events: list[dict[str, Any]], show_details: bool
) -> None:
    """
    Display all suspicious events or success message.

    Parameters
    ----------
    suspicious_events : list[dict[str, Any]]
        List of suspicious events detected
    show_details : bool
        Whether to show detailed autocomplete events
    """
    if suspicious_events:
        print("\nSuspicious events detected:", file=sys.stderr)

        # Sort events by their index for chronological display
        def get_sort_key(event: dict[str, Any]) -> int | float:
            if "event_indices" in event and event["event_indices"]:
                return event["event_indices"][0]
            if "detailed_events" in event and event["detailed_events"]:
                return event["detailed_events"][0].get("event_index", float("inf"))
            event_idx = event.get("event_index", -1)
            return event_idx if event_idx >= 0 else float("inf")

        sorted_events = sorted(suspicious_events, key=get_sort_key)

        for event in sorted_events:
            display_suspicious_event(event, show_details)
    else:
        print("Success! No suspicious events detected.", file=sys.stderr)


def display_template_diff(diff_text: str) -> None:
    """
    Display template diff output when verification fails.

    Parameters
    ----------
    diff_text : str
        Unified diff text between template and initial snapshot
    """
    if not diff_text:
        return

    print("\nTemplate mismatch diff:", file=sys.stderr)
    print(diff_text, file=sys.stderr)


def display_submitted_file_comparison(comparison: dict[str, Any] | None) -> None:
    """
    Display comparison results between reconstructed code and submitted file.

    Parameters
    ----------
    comparison : dict[str, Any] | None
        Comparison results from compare_submitted_file, or None if no comparison
    """
    if not comparison:
        return

    print("\nSubmitted file comparison:", file=sys.stderr)
    print(f"  Submitted file: {comparison['submitted_file']}", file=sys.stderr)

    if "error" in comparison:
        print(f"  Error: {comparison['error']}", file=sys.stderr)
        return

    if comparison["matches"]:
        print("  ✓ Reconstructed code matches submitted file exactly", file=sys.stderr)
    elif comparison.get("whitespace_only", False):
        print("  ⚠ Reconstructed code differs only in whitespace from submitted file", file=sys.stderr)
    else:
        print("  ✗ Reconstructed code differs from submitted file", file=sys.stderr)
        if comparison.get("diff"):
            print("\n  Diff (reconstructed → submitted):", file=sys.stderr)
            # Indent each line of the diff
            for line in comparison["diff"].split("\n"):
                if line:
                    print(f"    {line}", file=sys.stderr)


def print_separator() -> None:
    """Print a separator line."""
    print(f"{'='*80}", file=sys.stderr)


def print_batch_header(current: int, total: int, filename: str) -> None:
    """Print a batch processing header for a file."""
    print_separator()
    print(f"[{current}/{total}] Processing: {filename}", file=sys.stderr)
    print_separator()


def print_batch_summary(total: int, verified_count: int, failed_files: list[str]) -> None:
    """Print a summary of batch processing results."""
    print_separator()
    print(f"BATCH SUMMARY: Processed {total} files", file=sys.stderr)
    print_separator()
    print(f"Verified: {verified_count}/{total}", file=sys.stderr)

    if failed_files:
        print("\nFailed files:", file=sys.stderr)
        for filename in failed_files:
            print(f"  - {filename}", file=sys.stderr)
