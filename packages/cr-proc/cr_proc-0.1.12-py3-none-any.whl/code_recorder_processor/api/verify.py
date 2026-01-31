from typing import Any
from datetime import datetime
import difflib
from .document import normalize_path_string

# ============================================================================
# Constants for detection thresholds
# ============================================================================
MIN_WHITELIST_SIZE = 10  # Minimum fragment size to add to whitelist
MIN_MULTILINE_SIZE = 20  # Minimum size for multiline external paste detection
MIN_AUTOCOMPLETE_SIZE = 10  # Minimum size for autocomplete detection
MIN_RAPID_PASTE_CHARS = 5  # Minimum chars for a "paste" in rapid detection

def _normalize_newlines(text: str) -> str:
    """Normalize CRLF to LF to avoid offset and diff noise."""
    return text.replace("\r\n", "\n")


def is_only_whitespace_differences(template: str, actual: str) -> bool:
    """
    Return True if `actual` can be derived from `template` by changing only
    whitespace (spaces, tabs, newlines). All non-whitespace characters must
    appear in the same order with no additions, deletions, or substitutions.
    """
    t = _normalize_newlines(template)
    a = _normalize_newlines(actual)

    lt, la = len(t), len(a)
    i = j = 0

    while True:
        # Skip any whitespace on both sides
        while i < lt and t[i].isspace():
            i += 1
        while j < la and a[j].isspace():
            j += 1

        if i >= lt or j >= la:
            break

        if t[i] != a[j]:
            return False

        i += 1
        j += 1

    # Ensure no remaining non-whitespace characters on either side
    while i < lt:
        if not t[i].isspace():
            return False
        i += 1

    while j < la:
        if not a[j].isspace():
            return False
        j += 1

    return True


def verify_template(template: str, jsonData: tuple[dict[str, Any], ...]) -> str:
    """
    Verify the initial event is a faithful snapshot of the template,
    allowing only whitespace differences in the event's newFragment.

    Also validates that the recorder wrote an initial snapshot
    (oldFragment == newFragment on the first record).

    Returns the verified fragment text.
    Raises ValueError if verification fails.
    """
    if not jsonData:
        raise ValueError("jsonData is empty")

    first = jsonData[0]
    new_frag = _normalize_newlines(first["newFragment"])
    old_frag = _normalize_newlines(first["oldFragment"])
    temp_norm = _normalize_newlines(template)

    # Recorder must have written an initial full snapshot:
    if new_frag != old_frag:
        raise ValueError("oldFragment does not match newFragment (no initial snapshot)")

    # Accept exact match OR match that differs only by whitespace
    if new_frag == temp_norm:
        return new_frag

    if is_only_whitespace_differences(temp_norm, new_frag):
        return new_frag

    raise ValueError("newFragment does not match template (differs by more than whitespace)")


def template_diff(template: str, jsonData: tuple[dict[str, Any], ...]) -> str:
    """
    Produce a unified diff between the given template and the first event's newFragment.
    If the only differences are whitespace, return ''.
    """
    if not jsonData:
        return ""

    template_norm = _normalize_newlines(template)
    actual_norm = _normalize_newlines(jsonData[0]["newFragment"])

    # Suppress diff if only whitespace differences
    if is_only_whitespace_differences(template_norm, actual_norm):
        return ""

    # Generate a proper unified diff (headers on separate lines)
    t_lines = template_norm.splitlines(keepends=True)
    a_lines = actual_norm.splitlines(keepends=True)

    diff_iter = difflib.unified_diff(
        t_lines,
        a_lines,
        fromfile="template",
        tofile="actual",
        n=3,
        lineterm="\n",
    )
    return "".join(diff_iter)


def _build_document_states(jsonData: tuple[dict[str, Any], ...]) -> tuple[list[str], set[str]]:
    """
    Build complete document state at each event and a whitelist of all content seen.

    Reconstructs the document after each keystroke/edit to track what content
    existed in the document at each point in time. This allows detectors to
    check if pasted/autocompleted content already existed in the document.

    Only processes edit events (type="edit" or no type field for backwards compatibility).

    Parameters
    ----------
    jsonData : tuple[dict[str, Any], ...]
        The event data from the JSONL file (all event types)

    Returns
    -------
    tuple[list[str], set[str]]
        - List of document states (one per edit event, strings of full document content)
        - Set of all content fragments ever seen (whitelist for internal copy detection)
    """
    from .load import is_edit_event

    # Filter to only edit events
    edit_events = [e for e in jsonData if is_edit_event(e)]

    document_states = []
    content_whitelist = set()
    current_state = ""

    for idx, event in enumerate(edit_events):
        old_frag = _normalize_newlines(event.get("oldFragment", ""))
        new_frag = _normalize_newlines(event.get("newFragment", ""))
        offset = event.get("offset", 0)

        # First event is the initial snapshot (template)
        if idx == 0:
            current_state = new_frag
        elif new_frag != old_frag:
            # Apply the edit to reconstruct document state
            current_state = current_state[:offset] + new_frag + current_state[offset + len(old_frag):]

        document_states.append(current_state)

        # Build whitelist of all content fragments seen
        # Add both old and new fragments to whitelist for comprehensive coverage
        if len(old_frag) > MIN_WHITELIST_SIZE:
            content_whitelist.add(old_frag)
        if len(new_frag) > MIN_WHITELIST_SIZE:
            content_whitelist.add(new_frag)

        # Also add the full document state to whitelist
        if len(current_state) > MIN_WHITELIST_SIZE:
            content_whitelist.add(current_state)

    return document_states, content_whitelist


def _detect_multiline_external_pastes(
    jsonData: tuple[dict[str, Any], ...],
    document_states: list[str],
    content_whitelist: set[str]
) -> list[dict[str, Any]]:
    """
    Detect multi-line copy-paste events from external sources.

    Flags newFragments that are significant in length (more than one line)
    and do not appear to be copied from within the document itself.

    Only processes edit events (type="edit" or no type field for backwards compatibility).

    Parameters
    ----------
    jsonData : tuple[dict[str, Any], ...]
        The event data (all event types)
    document_states : list[str]
        Full document state at each edit event
    content_whitelist : set[str]
        All content fragments ever seen in the document (for internal copy detection)

    Returns
    -------
    list[dict[str, Any]]
        List of suspicious multi-line paste events.
    """
    from .load import is_edit_event

    # Filter to only edit events
    edit_events = [e for e in jsonData if is_edit_event(e)]

    suspicious_events = []

    # Build whitelist incrementally to only include content from BEFORE each event
    past_whitelist = set()

    for idx, event in enumerate(edit_events):
        old_frag = _normalize_newlines(event.get("oldFragment", ""))
        new_frag = _normalize_newlines(event.get("newFragment", ""))

        # Skip if no actual change
        if new_frag == old_frag or new_frag.strip() == "":
            pass  # Still add to whitelist below
        # Only check multi-line content (more than 2 lines means at least 2 actual lines)
        elif len(new_frag.split("\n")) > 2:
            new_lines = new_frag.split("\n")

            # Check if the new content already existed in the document at any prior point
            is_internal_copy = False

            # Check against document state BEFORE this event
            if idx > 0:
                prior_state = document_states[idx - 1]
                if new_frag in prior_state:
                    is_internal_copy = True

            # Also check against whitelist of content from BEFORE this event
            if not is_internal_copy:
                for hist_content in past_whitelist:
                    # Ignore tiny fragments - multiline external pastes should be significant
                    if len(hist_content) < MIN_MULTILINE_SIZE:
                        continue

                    # Require substantial overlap in size to count as an internal copy
                    similar_length = (
                        len(hist_content) >= 0.8 * len(new_frag)
                        and len(hist_content) <= 1.25 * len(new_frag)
                    )

                    if new_frag == hist_content:
                        is_internal_copy = True
                        break

                    if new_frag in hist_content and similar_length:
                        is_internal_copy = True
                        break

                    if hist_content in new_frag and similar_length:
                        is_internal_copy = True
                        break

            # Also check if it's in the old fragment (internal move/copy)
            if not is_internal_copy and old_frag and (new_frag in old_frag or old_frag in new_frag):
                is_internal_copy = True

            if not is_internal_copy:
                suspicious_events.append({
                    "event_index": idx,
                    "line_count": len(new_lines),
                    "char_count": len(new_frag),
                    "reason": "multi-line external paste",
                    "newFragment": new_frag
                })

        # Add current event's content to whitelist for future events
        if len(old_frag) > MIN_MULTILINE_SIZE:
            past_whitelist.add(old_frag)
        if len(new_frag) > MIN_MULTILINE_SIZE:
            past_whitelist.add(new_frag)
        if idx > 0 and len(document_states[idx - 1]) > MIN_MULTILINE_SIZE:
            past_whitelist.add(document_states[idx - 1])

    return suspicious_events


def _detect_rapid_paste_sequences(jsonData: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    """
    Detect rapid sequences of one-line pastes (AI assistance indicator).

    Identifies clusters of 3+ one-line paste events occurring within 1 second,
    which may indicate AI-assisted code generation.

    Only processes edit events (type="edit" or no type field for backwards compatibility).

    Returns a list of suspicious rapid-paste events.
    """
    from .load import is_edit_event

    # Filter to only edit events
    edit_events = [e for e in jsonData if is_edit_event(e)]

    suspicious_events = []

    # Track one-line paste events for rapid-paste detection
    one_line_pastes = []

    for idx, event in enumerate(edit_events):
        new_frag = _normalize_newlines(event.get("newFragment", ""))
        old_frag = _normalize_newlines(event.get("oldFragment", ""))
        timestamp = event.get("timestamp")

        # Skip if no timestamp or no change
        if not timestamp or new_frag == old_frag or new_frag.strip() == "":
            continue

        # Check if newFragment is a single line (2 elements = 1 line + trailing \n)
        new_lines = new_frag.split("\n")
        if len(new_lines) == 2:
            # Heuristic: if it's more than a few characters, it might be pasted
            if len(new_frag.strip()) > MIN_RAPID_PASTE_CHARS:
                one_line_pastes.append({
                    "event_index": idx,
                    "timestamp": timestamp,
                    "content": new_frag
                })

    # Analyze one-line pastes for rapid clusters
    if not one_line_pastes:
        return suspicious_events

    def parse_ts(ts_str: str) -> datetime:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))

    i = 0
    while i < len(one_line_pastes):
        cluster = [one_line_pastes[i]]
        cluster_start = parse_ts(one_line_pastes[i]["timestamp"])

        # Look ahead for more pastes within 1 second
        j = i + 1
        while j < len(one_line_pastes):
            current_time = parse_ts(one_line_pastes[j]["timestamp"])
            if (current_time - cluster_start).total_seconds() <= 1.0:
                cluster.append(one_line_pastes[j])
                j += 1
            else:
                break

        # If we found 3+ one-line pastes within 1 second, flag it
        if len(cluster) >= 3:
            event_indices = [p["event_index"] for p in cluster]

            # Build detailed events list for optional detailed review
            detailed_events = []
            for paste in cluster:
                idx = paste["event_index"]
                content = paste["content"]
                detailed_events.append({
                    "event_index": idx,
                    "line_count": 1,
                    "char_count": len(content),
                    "newFragment": content,
                })

            suspicious_events.append({
                "event_index": event_indices[0],
                "event_indices": event_indices,
                "line_count": len(cluster),
                "char_count": sum(len(p["content"]) for p in cluster),
                "reason": "rapid one-line pastes (AI indicator)",
                "newFragment": f"{len(cluster)} one-line pastes in 1 second",
                "detailed_events": detailed_events,
            })

        i = j if j > i + 1 else i + 1

    return suspicious_events


def _detect_fullline_autocomplete(
    jsonData: tuple[dict[str, Any], ...],
    document_states: list[str],
    content_whitelist: set[str],
    excluded_indices: set[int]
) -> list[dict[str, Any]]:
    """
    Detect multi-line auto-complete events where the IDE/AI generates multiple complete lines.

    Focuses on significant AI assistance where the system generates entire functions or blocks
    (2+ lines) in a single completion event. This is distinct from basic IDE autocomplete
    (e.g., finishing a function name).

    At keystroke level, events show:
    - Normal typing: oldFragment="" (empty), newFragment="X" (1 char)
    - Basic autocomplete: oldFragment="" (empty), newFragment="function_name" (IDE suggests identifier)
    - Full-line AI completion: oldFragment="" (empty), newFragment="def foo():\n    pass" (entire function)

    Full-line auto-complete is detected when:
    - oldFragment is empty or very short (0-3 chars)
    - newFragment generates 2+ complete lines
    - newFragment contains complete statements (not just identifiers)
    - Content represents meaningful code structure
    - newFragment does NOT already exist in the document state
    - Event not already flagged as external copy-paste

    Only processes edit events (type="edit" or no type field for backwards compatibility).

    Parameters
    ----------
    jsonData : tuple[dict[str, Any], ...]
        The event data (all event types)
    document_states : list[str]
        Full document state at each edit event
    content_whitelist : set[str]
        All content fragments ever seen in the document
    excluded_indices : set[int]
        Set of event indices already flagged by other detectors (to avoid double-flagging)

    Returns
    -------
    list[dict[str, Any]]
        List of suspected multi-line auto-complete events.
    """
    from .load import is_edit_event

    # Filter to only edit events
    edit_events = [e for e in jsonData if is_edit_event(e)]

    suspicious_events = []

    # Build whitelist incrementally to only include content from BEFORE each event
    past_whitelist = set()

    for idx, event in enumerate(edit_events):
        # Skip if already flagged by another detector
        if idx in excluded_indices:
            past_whitelist_update(idx, event, document_states, past_whitelist)
            continue

        old_frag = _normalize_newlines(event.get("oldFragment", ""))
        new_frag = _normalize_newlines(event.get("newFragment", ""))

        # Skip first event (template) and no-change events
        if idx == 0 or new_frag == old_frag:
            past_whitelist_update(idx, event, document_states, past_whitelist)
            continue

        old_len = len(old_frag)
        new_len = len(new_frag)

        # At keystroke level, oldFragment is typically empty for insertions
        # Allow up to 3 chars for prefix-based triggers (e.g., "de" -> "def")
        if old_len > 3:
            past_whitelist_update(idx, event, document_states, past_whitelist)
            continue

        # Check line count - we care about complete statements
        # Multi-line is obviously concerning, but single-line with a complete statement
        # (like "if x: return True") is also suspicious if it came from autocomplete
        new_lines = [n for n in new_frag.split("\n") if n.strip() != ""]

        # For single-line completions, be more strict about what we flag
        # We only flag if it's a complete statement with keywords, not just identifier completion
        is_single_line = len(new_lines) <= 2  # 2 elements = 1 line + trailing \n
        is_multi_line = len(new_lines) >= 3   # 3+ elements = 2+ actual lines

        if not (is_single_line or is_multi_line):
            # Shouldn't happen, but skip if malformed
            past_whitelist_update(idx, event, document_states, past_whitelist)
            continue

        # The new fragment should not be just whitespace
        if not new_frag.strip():
            past_whitelist_update(idx, event, document_states, past_whitelist)
            continue

        # Check if the new fragment contains code structure indicators
        # These strongly suggest IDE/AI auto-completion of actual code (not just identifiers)
        complete_statement_indicators = [
            ":",      # Block statement (if:, for:, def:, class:, while:, with:, etc.)
            "return", # Return statement
            "def ",   # Function definition
            "class ", # Class definition
            "if ",    # If statement
            "for ",   # For loop
            "while ", # While loop
            "try:",   # Try block
            "except", # Exception handling
            "import ", # Import statement
            "=",      # Assignment
        ]

        has_complete_statement = any(indicator in new_frag for indicator in complete_statement_indicators)

        if not has_complete_statement:
            # No complete statement - skip basic identifier completion
            past_whitelist_update(idx, event, document_states, past_whitelist)
            continue

        # Minimum size for meaningful completion
        if new_len < MIN_AUTOCOMPLETE_SIZE:
            past_whitelist_update(idx, event, document_states, past_whitelist)
            continue

        # For multi-line: maximum size to distinguish from external pastes
        # External pastes are typically much larger (100+ chars)
        # Multi-line completions are usually 20-300 chars for a small function/block
        if is_multi_line and new_len > 300:
            past_whitelist_update(idx, event, document_states, past_whitelist)
            continue

        # For single-line: could be larger due to chained methods or long statements
        # but cap at 200 chars to avoid flagging user-typed long lines
        if is_single_line and new_len > 200:
            past_whitelist_update(idx, event, document_states, past_whitelist)
            continue

        # Check if this content already existed in the document state BEFORE this event
        is_internal_copy = False

        if idx > 0:
            prior_state = document_states[idx - 1]
            if new_frag in prior_state:
                is_internal_copy = True

        # Also check against whitelist of content from BEFORE this event
        if not is_internal_copy:
            for hist_content in past_whitelist:
                # Ignore tiny fragments
                if len(hist_content) < MIN_AUTOCOMPLETE_SIZE:
                    continue

                # Check for exact match or significant overlap
                if new_frag == hist_content:
                    is_internal_copy = True
                    break

                # Check for substring matches with similar length
                similar_length = (
                    len(hist_content) >= 0.8 * len(new_frag)
                    and len(hist_content) <= 1.25 * len(new_frag)
                )

                if (new_frag in hist_content or hist_content in new_frag) and similar_length:
                    is_internal_copy = True
                    break

        if not is_internal_copy:
            line_desc = "line" if is_single_line else "lines"
            suspicious_events.append({
                "event_index": idx,
                "line_count": len(new_lines),
                "char_count": new_len,
                "reason": f"complete statement auto-complete (AI assistance)",
                "newFragment": new_frag,
            })

        # Add current event's content to whitelist for future events
        past_whitelist_update(idx, event, document_states, past_whitelist)

    return suspicious_events


def past_whitelist_update(
    idx: int,
    event: dict[str, Any],
    document_states: list[str],
    past_whitelist: set[str]
) -> None:
    """Helper to update the past_whitelist with content from current event."""
    old_frag = _normalize_newlines(event.get("oldFragment", ""))
    new_frag = _normalize_newlines(event.get("newFragment", ""))

    if len(old_frag) > MIN_AUTOCOMPLETE_SIZE:
        past_whitelist.add(old_frag)
    if len(new_frag) > MIN_AUTOCOMPLETE_SIZE:
        past_whitelist.add(new_frag)
    if idx < len(document_states) and len(document_states[idx]) > MIN_AUTOCOMPLETE_SIZE:
        past_whitelist.add(document_states[idx])


def detect_external_copypaste(jsonData: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    """
    Detect copy-paste events from external sources and AI-assisted coding patterns.

    Combines detection of:
    1. Multi-line external paste events (content not from within document)
    2. Rapid one-line paste sequences (potential AI assistance indicator)
    3. Full-line auto-complete events (user types, AI completes the line)

    Detection order matters: events flagged by earlier detectors are excluded
    from later detectors to avoid double-flagging.

    Returns a list of all suspicious events with metadata, including aggregate statistics.
    """
    suspicious_events = []

    # Build shared document state tracking
    # This reconstructs the full document at each event and creates a whitelist
    # of all content that has ever appeared in the document
    document_states, content_whitelist = _build_document_states(jsonData)

    # Step 1: Detect multi-line external pastes
    multiline_events = _detect_multiline_external_pastes(jsonData, document_states, content_whitelist)
    suspicious_events.extend(multiline_events)

    # Step 2: Detect rapid one-line paste sequences (AI indicator)
    rapid_paste_events = _detect_rapid_paste_sequences(jsonData)
    suspicious_events.extend(rapid_paste_events)

    # Build set of all event indices already flagged
    excluded_indices = set()
    for event in multiline_events:
        # Handle both single events and clusters
        if "event_indices" in event:
            excluded_indices.update(event["event_indices"])
        else:
            excluded_indices.add(event["event_index"])

    for event in rapid_paste_events:
        if "event_indices" in event:
            excluded_indices.update(event["event_indices"])
        else:
            excluded_indices.add(event["event_index"])

    # Step 3: Detect full-line auto-complete events (excluding already-flagged events)
    autocomplete_events = _detect_fullline_autocomplete(
        jsonData, document_states, content_whitelist, excluded_indices
    )

    # Calculate aggregate statistics for auto-complete/small paste events
    # Store individual events for optional detailed review, but don't report them by default
    if autocomplete_events:
        total_autocomplete_chars = sum(ev["char_count"] for ev in autocomplete_events)
        total_autocomplete_events = len(autocomplete_events)

        # Always add aggregate summary, never individual events
        # Store individual events in the aggregate for optional detailed review
        suspicious_events.append({
            "event_index": -1,  # Special marker for aggregate
            "event_count": total_autocomplete_events,
            "total_chars": total_autocomplete_chars,
            "reason": "aggregate auto-complete/small paste activity",
            "newFragment": f"{total_autocomplete_events} auto-complete events ({total_autocomplete_chars} total chars)",
            "detailed_events": autocomplete_events,  # Store for optional review
        })

    return suspicious_events


def check_time_limit(jsonData: tuple[dict[str, Any], ...], time_limit_minutes: int | None) -> dict[str, Any] | None:
    """
    Check if the time between first and last edit exceeds the specified time limit.

    Tracks elapsed editing time across sessions by summing actual editing time within
    each session (excluding gaps between sessions). Focus events (type="focusStatus")
    are used to pause time tracking when the window loses focus for extended periods.

    Time tracking behavior:
    - Tracks actual editing time by looking at timestamps between edit events
    - When a focusStatus event with focused=false is encountered, time tracking pauses
    - Time tracking resumes when a focusStatus event with focused=true is encountered
    - Gaps > 5 minutes while unfocused are excluded from time tracking
    - Gaps <= 5 minutes are counted even when unfocused (student thinking/reviewing)

    Parameters
    ----------
    jsonData : tuple[dict[str, Any], ...]
        The event data from the JSONL file (all event types)
    time_limit_minutes : int | None
        Maximum allowed time in minutes between first and last overall edit.
        If None, no time limit is enforced.

    Returns
    -------
    dict[str, Any] | None
        A dictionary with time limit and elapsed time info.
        Contains 'exceeds_limit' flag and always includes 'minutes_elapsed'.
    """
    if not jsonData:
        return None

    def parse_ts(ts_str: str) -> datetime:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))

    # Separate edit events from focus events
    from .load import is_edit_event

    edit_events = [e for e in jsonData if is_edit_event(e)]
    focus_events = [e for e in jsonData if e.get("type") == "focusStatus"]

    if not edit_events:
        return None

    # Identify session boundaries: sessions start at indices where offset == 0
    # (indicating file reopen/recording restart) and oldFragment == newFragment (initial snapshot)
    session_starts = [0]  # First session always starts at index 0
    for idx in range(1, len(edit_events)):
        offset = edit_events[idx].get("offset", -1)
        old_frag = edit_events[idx].get("oldFragment", "")
        new_frag = edit_events[idx].get("newFragment", "")
        # Session boundary: offset is 0 and it's an initial snapshot (old == new, non-empty)
        if offset == 0 and old_frag == new_frag and old_frag.strip() != "":
            session_starts.append(idx)

    # Add sentinel to mark end of last session
    session_starts.append(len(edit_events))

    # Find first and last timestamps overall
    first_timestamp_overall = None
    last_timestamp_overall = None

    for event in edit_events:
        if event.get("timestamp"):
            if first_timestamp_overall is None:
                first_timestamp_overall = event["timestamp"]
            last_timestamp_overall = event["timestamp"]

    if first_timestamp_overall is None or last_timestamp_overall is None:
        # Not enough events with timestamps
        return None

    # Build a focus status timeline from focus events
    # Map timestamp -> focused (True/False)
    focus_timeline: list[tuple[datetime, bool]] = []
    for focus_event in focus_events:
        if "timestamp" in focus_event and "focused" in focus_event:
            try:
                ts = parse_ts(focus_event["timestamp"])
                focused = focus_event["focused"]
                focus_timeline.append((ts, focused))
            except (ValueError, KeyError):
                continue

    # Sort by timestamp
    focus_timeline.sort(key=lambda x: x[0])

    def is_focused_at(timestamp: datetime) -> bool:
        """Check if the window was focused at the given timestamp."""
        # Walk backwards through focus events to find the most recent state
        for ts, focused in reversed(focus_timeline):
            if ts <= timestamp:
                return focused
        # Default to focused if no prior focus event found
        return True

    # Calculate elapsed time by summing editing time within each session
    # with focus-aware gap handling
    total_minutes_elapsed = 0.0
    UNFOCUSED_GAP_THRESHOLD_MINUTES = 5.0  # Don't count gaps > 5 min when unfocused

    for i in range(len(session_starts) - 1):
        session_start = session_starts[i]
        session_end = session_starts[i + 1]

        # Collect all timestamped events in this session
        session_events: list[tuple[datetime, int]] = []
        for idx in range(session_start, session_end):
            event = edit_events[idx]
            timestamp = event.get("timestamp")
            if timestamp:
                try:
                    event_time = parse_ts(timestamp)
                    session_events.append((event_time, idx))
                except (ValueError, KeyError):
                    continue

        if not session_events:
            continue

        # Sort by timestamp
        session_events.sort(key=lambda x: x[0])

        # Calculate time by summing gaps between consecutive events
        for j in range(len(session_events) - 1):
            current_time, _ = session_events[j]
            next_time, _ = session_events[j + 1]

            gap_seconds = (next_time - current_time).total_seconds()
            gap_minutes = gap_seconds / 60

            # Check focus status at the end of this gap (next_time)
            # If unfocused and gap is large, don't count it
            if not is_focused_at(next_time) and gap_minutes > UNFOCUSED_GAP_THRESHOLD_MINUTES:
                # Skip this gap - student was away from editor
                continue

            total_minutes_elapsed += gap_minutes

    # For time limit check, use the span from first to last timestamp overall
    try:
        first_time_overall = parse_ts(first_timestamp_overall)
        last_time_overall = parse_ts(last_timestamp_overall)
        overall_span_minutes = (last_time_overall - first_time_overall).total_seconds() / 60
    except (ValueError, KeyError):
        # Timestamp parsing failed
        return None

    result = {
        "time_limit_minutes": time_limit_minutes,
        "minutes_elapsed": round(total_minutes_elapsed, 2),
        "first_timestamp": first_timestamp_overall,
        "last_timestamp": last_timestamp_overall,
    }

    # For time limit check, compare the overall span (first to last timestamp) against the limit
    if time_limit_minutes is not None:
        result["exceeds_limit"] = overall_span_minutes > time_limit_minutes
    else:
        result["exceeds_limit"] = False

    return result


def verify(template: str, jsonData: tuple[dict[str, Any], ...]) -> tuple[str, list[dict[str, Any]]]:
    """
    Comprehensive verification of recorded code events.

    Performs:
    1. Template verification (initial snapshot matches template)
    2. External copy-paste detection

    Returns:
        tuple: (verified_template_text, list_of_suspicious_copypaste_events)

    Raises:
        ValueError: If template verification fails
    """
    # Verify template
    verified_template = verify_template(template, jsonData)

    # Detect external copy-paste events
    suspicious_events = detect_external_copypaste(jsonData)

    return verified_template, suspicious_events


def combine_time_info(
    all_events: list[tuple[dict[str, Any], ...]], time_limit_minutes: int | None
) -> dict[str, Any] | None:
    """
    Combine time information from multiple recording files, avoiding double-counting overlapping time.

    Merges all events from multiple recordings, then calculates the actual time spent editing
    using the same logic as check_time_limit (gap analysis with focus awareness). This ensures
    overlapping editing sessions are not double-counted.

    Parameters
    ----------
    all_events : list[tuple[dict[str, Any], ...]]
        List of event tuples from multiple recording files
    time_limit_minutes : int | None
        Time limit to check against

    Returns
    -------
    dict[str, Any] | None
        Combined time information, or None if no valid data
    """
    # Filter out empty event sets
    valid_event_sets = [events for events in all_events if events]
    if not valid_event_sets:
        return None

    # Merge all events from all recordings into a single tuple
    merged_events = tuple(
        event
        for event_set in valid_event_sets
        for event in event_set
    )

    # Use check_time_limit on the merged events to calculate time properly
    # This handles overlapping periods automatically since we're now analyzing
    # all events together chronologically
    combined_result = check_time_limit(merged_events, time_limit_minutes)

    if combined_result is None:
        return None

    # Add file_count to the result
    combined_result["file_count"] = len(valid_event_sets)

    return combined_result


def compare_submitted_file(reconstructed_code: str, submitted_file_path) -> dict[str, Any]:
    """
    Compare reconstructed code from recording with a submitted final file.

    Parameters
    ----------
    reconstructed_code : str
        The code reconstructed from the recording
    submitted_file_path : Path
        Path to the submitted file

    Returns
    -------
    dict[str, Any]
        Dictionary containing:
        - matches: bool indicating if the files match
        - submitted_file: path to the submitted file
        - diff: unified diff string if files don't match
        - whitespace_only: bool indicating if only whitespace differs
    """
    try:
        submitted_content = submitted_file_path.read_text()
    except Exception as e:
        return {
            "matches": False,
            "submitted_file": normalize_path_string(str(submitted_file_path)),
            "error": f"Failed to read submitted file: {e}",
            "diff": "",
            "whitespace_only": False,
        }

    # Normalize newlines for comparison
    reconstructed_normalized = _normalize_newlines(reconstructed_code)
    submitted_normalized = _normalize_newlines(submitted_content)

    # Check exact match
    matches = reconstructed_normalized == submitted_normalized

    # Check if only whitespace differs
    whitespace_only = False
    if not matches:
        whitespace_only = is_only_whitespace_differences(
            submitted_normalized, reconstructed_normalized
        )

    # Generate diff if they don't match
    diff_text = ""
    if not matches:
        reconstructed_lines = reconstructed_normalized.splitlines(keepends=True)
        submitted_lines = submitted_normalized.splitlines(keepends=True)
        diff = difflib.unified_diff(
            reconstructed_lines,
            submitted_lines,
            fromfile="reconstructed",
            tofile="submitted",
            lineterm="",
        )
        diff_text = "".join(diff)

    return {
        "matches": matches,
        "submitted_file": normalize_path_string(str(submitted_file_path)),
        "diff": diff_text,
        "whitespace_only": whitespace_only,
    }
