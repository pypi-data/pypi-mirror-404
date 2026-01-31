"""Playback functionality for viewing code evolution."""
import os
import sys
import time
from datetime import datetime
from typing import Any


def playback_recording(
    json_data: tuple[dict[str, Any], ...],
    document: str,
    template: str,
    speed: float = 1.0,
) -> None:
    """
    Play back a recording, showing the code evolving in real-time.

    Only plays back edit events (type="edit" or no type field for backwards compatibility).

    Parameters
    ----------
    json_data : tuple[dict[str, Any], ...]
        The recording events (all event types)
    document : str
        The document to play back
    template : str
        The initial template content
    speed : float
        Playback speed multiplier (1.0 = real-time, 2.0 = 2x speed, 0.5 = half speed)
    """
    # Filter to only edit events (backwards compatible)
    from .api.load import is_edit_event
    edit_events = [e for e in json_data if is_edit_event(e)]

    # Filter events for the target document
    doc_events = [e for e in edit_events if e.get("document") == document]

    if not doc_events:
        print(f"No events found for document: {document}", file=sys.stderr)
        return

    # Start with template
    current_content = template
    last_timestamp = None

    def clear_screen():
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def parse_timestamp(ts_str: str) -> datetime:
        """Parse ISO timestamp string."""
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))

    # Show initial template
    clear_screen()
    print(f"=" * 80)
    print(f"PLAYBACK: {document} (Speed: {speed}x)")
    print(f"Event 0 / {len(doc_events)} - Initial Template")
    print(f"=" * 80)
    print(current_content)
    print(f"\n{'=' * 80}")
    print("Press Ctrl+C to stop playback")
    time.sleep(2.0 / speed)

    try:
        for idx, event in enumerate(doc_events, 1):
            old_frag = event.get("oldFragment", "")
            new_frag = event.get("newFragment", "")
            offset = event.get("offset", 0)
            timestamp = event.get("timestamp")

            # Calculate delay based on timestamp difference
            if last_timestamp and timestamp:
                try:
                    ts1 = parse_timestamp(last_timestamp)
                    ts2 = parse_timestamp(timestamp)
                    delay = (ts2 - ts1).total_seconds() / speed
                    # Cap delay at 5 seconds for very long pauses
                    delay = min(delay, 5.0)
                    if delay > 0:
                        time.sleep(delay)
                except (ValueError, KeyError):
                    time.sleep(0.1 / speed)
            else:
                time.sleep(0.1 / speed)

            last_timestamp = timestamp

            # Apply the edit
            if new_frag != old_frag:
                current_content = current_content[:offset] + new_frag + current_content[offset + len(old_frag):]

            # Display current state
            clear_screen()
            print(f"=" * 80)
            print(f"PLAYBACK: {document} (Speed: {speed}x)")
            print(f"Event {idx} / {len(doc_events)} - {timestamp or 'unknown time'}")

            # Show what changed
            if new_frag != old_frag:
                change_type = "INSERT" if not old_frag else ("DELETE" if not new_frag else "REPLACE")
                print(f"Action: {change_type} at offset {offset} ({len(new_frag)} chars)")

            print(f"=" * 80)
            print(current_content)
            print(f"\n{'=' * 80}")
            print(f"Progress: [{('#' * (idx * 40 // len(doc_events))).ljust(40)}] {idx}/{len(doc_events)}")
            print("Press Ctrl+C to stop playback")

    except KeyboardInterrupt:
        print("\n\nPlayback stopped by user.", file=sys.stderr)
        return

    # Final summary
    print("\n\nPlayback complete!", file=sys.stderr)
    print(f"Total events: {len(doc_events)}", file=sys.stderr)
