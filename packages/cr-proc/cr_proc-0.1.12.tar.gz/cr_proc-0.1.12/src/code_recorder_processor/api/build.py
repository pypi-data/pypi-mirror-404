from datetime import datetime
from typing import  Any, Optional


def _parse_ts(ts: str) -> datetime:
    """Parse ISO 8601 timestamps that end with 'Z' (UTC)."""
    # Convert trailing Z to +00:00 for fromisoformat
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _normalize_newlines(text: str) -> str:
    """Normalize CRLF to LF for consistent offset handling."""
    return text.replace("\r\n", "\n")


def _apply_event_exact_text(doc: str, offset: int, old: str, new: str) -> str:
    """Apply an event assuming Python string indices (Unicode code points)."""
    return doc[:offset] + new + doc[offset + len(old):]


def _apply_event_fuzzy_text(doc: str, offset: int, old: str, new: str, window: int) -> str:
    """
    Apply an event with a fuzzy fallback in Python string space:
    - If old == '', it's a pure insertion at offset (clamped).
    - If exact match fails, search for old around the offset within ±window chars and
      replace the nearest occurrence.
    """
    if old == "":
        off = max(0, min(offset, len(doc)))
        return doc[:off] + new + doc[off:]

    # Try exact match first
    if doc[offset:offset + len(old)] == old:
        return _apply_event_exact_text(doc, offset, old, new)

    # Fuzzy search around the offset
    start = max(0, offset - window)
    end = min(len(doc), offset + window)
    best_pos, best_dist = None, None

    i = start
    while True:
        i = doc.find(old, i, end)
        if i == -1:
            break
        dist = abs(i - offset)
        if best_dist is None or dist < best_dist:
            best_pos, best_dist = i, dist
        i += 1

    if best_pos is not None:
        return _apply_event_exact_text(doc, best_pos, old, new)

    raise ValueError(
        f"Old fragment not found near offset {offset}.\nold={old!r}\nnew={new!r}"
    )


def _apply_event_exact_utf16(doc_bytes: bytes, offset_units: int, old: str, new: str) -> bytes:
    """
    Apply an event in UTF-16-LE byte space (JetBrains Document uses UTF-16 code units):
    offset_units is measured in code units; each unit is 2 bytes in UTF-16-LE.
    """
    # Convert offset in code units to byte index
    bidx = offset_units * 2
    old_b = old.encode("utf-16-le")
    new_b = new.encode("utf-16-le")
    return doc_bytes[:bidx] + new_b + doc_bytes[bidx + len(old_b):]


def _apply_event_fuzzy_utf16(doc_bytes: bytes, offset_units: int, old: str, new: str, window_units: int) -> bytes:
    """
    Fuzzy apply in UTF-16-LE byte space:
    - If old == '', pure insertion at offset_units.
    - Else try exact match, otherwise search for old within ±window_units and replace nearest occurrence.
    """
    bidx = offset_units * 2
    old_b = old.encode("utf-16-le")
    new_b = new.encode("utf-16-le")

    if old == "":
        # Insertion: clamp to bounds
        bidx = max(0, min(bidx, len(doc_bytes)))
        return doc_bytes[:bidx] + new_b + doc_bytes[bidx:]

    # Exact match
    if doc_bytes[bidx:bidx + len(old_b)] == old_b:
        return _apply_event_exact_utf16(doc_bytes, offset_units, old, new)

    # Fuzzy search around offset
    start_b = max(0, bidx - window_units * 2)
    end_b = min(len(doc_bytes), bidx + window_units * 2)

    best_pos_b, best_dist_units = None, None
    i = start_b
    while True:
        i = doc_bytes.find(old_b, i, end_b)
        if i == -1:
            break
        dist_units = abs((i // 2) - offset_units)
        if best_dist_units is None or dist_units < best_dist_units:
            best_pos_b, best_dist_units = i, dist_units
        i += 1

    if best_pos_b is not None:
        return doc_bytes[:best_pos_b] + new_b + doc_bytes[best_pos_b + len(old_b):]

    raise ValueError(
        f"Old fragment not found near offset {offset_units} (UTF-16 units).\n"
        f"old={old!r}\nnew={new!r}"
    )


def reconstruct_file_from_events(
    events: tuple[dict[str, Any], ...],
    template: str,
    document_path: Optional[str] = None,
    *,
    utf16_mode: bool = False,
    window: int = 200,
    normalize_newlines: bool = True,
) -> str:
    """
    Reconstruct the final document by replaying PyCharm/IntelliJ edit events.

    Parameters
    ----------
    events : tuple of dict
        Each dict should contain:
          - 'type': (optional) event type - only 'edit' events or events without
            type field are processed (backwards compatible)
          - 'timestamp': ISO 8601 string, e.g., '2026-01-13T22:40:44.137341Z'
          - 'document': absolute path string of the edited file
          - 'offset': integer offset (JetBrains Document uses UTF-16 code units)
          - 'oldFragment': string being replaced/removed at offset
          - 'newFragment': string inserted at offset
    template_path : Path
        Path to the template file content to use as the starting point.
    document_path : Optional[str]
        If provided, only events matching this path will be applied. If None,
        the function tries to infer:
          - If any event matches str(template_path), use those.
          - If there's only one distinct document in events, use that.
          - Otherwise raises ValueError.
    utf16_mode : bool (default: False)
        If True, treat offsets as UTF-16 code units and apply changes in UTF-16-LE
        byte space (safer for emoji/astral chars). If False, operate on Python
        string indices (fine for ASCII/BMP-only source).
    window : int (default: 200)
        Fuzzy search window radius around the intended offset. Used when exact
        match of oldFragment at offset fails; the nearest occurrence within the
        window is replaced.
    normalize_newlines : bool (default: True)
        If True, normalize CRLF to LF in the starting template content. This
        prevents offset drift if events were recorded using LF.

    Returns
    -------
    str
        The reconstructed final document content.

    Raises
    ------
    ValueError
        - If the target document cannot be determined.
        - If an edit cannot be applied (oldFragment not found near offset).
    """
    # Filter to only edit events (backwards compatible with old format)
    from .load import is_edit_event
    events = tuple(e for e in events if is_edit_event(e))

    # Skip no-op events (oldFragment == newFragment, typically file-open markers)
    events = tuple(e for e in events if not (e.get("oldFragment") == e.get("newFragment") and e.get("offset") == 0))

    # Read template content
    if normalize_newlines:
        template = _normalize_newlines(template)

    # Decide which document's events to replay
    docs = {e.get("document") for e in events}
    target_doc = document_path
    template_doc_str = str(template)

    if target_doc is None:
        if template_doc_str in docs:
            target_doc = template_doc_str
        elif len(docs) == 1:
            target_doc = next(iter(docs))
        else:
            raise ValueError(
                "Ambiguous target document: provide document_path explicitly. "
                f"Found documents: {sorted(d for d in docs if d is not None)}"
            )

    # Filter events to the target document and sort by timestamp
    evs = [e for e in events if e.get("document") == target_doc]
    evs.sort(key=lambda e: _parse_ts(e["timestamp"]))

    if not evs:
        # No events for target_doc; return template unchanged
        return template

    # Handle case where first event is a file-open/load event at offset 0
    # (IDE captures the file content as seen when opened)
    if evs and evs[0].get("offset") == 0:
        first_old = evs[0].get("oldFragment", "")
        first_new = evs[0].get("newFragment", "")

        if first_old and not template.startswith(first_old):
            # Check if this looks like a file-open event:
            # - First event is at offset 0
            # - oldFragment and newFragment contain significant content (file was loaded)
            # - Template is much smaller (stub/placeholder)
            is_likely_file_open = (
                first_old == first_new and  # no-op replacement (just file load)
                len(first_old) > 50 and      # substantial content
                len(template) < len(first_old)  # template is smaller stub
            )

            if is_likely_file_open:
                # Use first event's oldFragment as the template (actual file state when opened)
                template = first_old
            else:
                # Template genuinely doesn't match
                raise ValueError(
                    f"Template content does not match recording's initial state.\n"
                    f"First event expects to replace {len(first_old)} chars starting at offset 0,\n"
                    f"but template only has {len(template)} chars and starts with:\n"
                    f"{template[:min(100, len(template))]!r}\n\n"
                    f"Expected to start with:\n"
                    f"{first_old[:min(100, len(first_old))]!r}\n\n"
                    f"Recording was likely made on a different version of the file.\n"
                    f"Document path in recording: {target_doc}"
                )

    if utf16_mode:
        # Work in UTF-16-LE byte space
        doc_bytes = template.encode("utf-16-le")
        for e in evs:
            offset_units = int(e["offset"])
            old = e.get("oldFragment", "")
            new = e.get("newFragment", "")
            doc_bytes = _apply_event_fuzzy_utf16(doc_bytes, offset_units, old, new, window_units=window)
        # Decode back to text
        return doc_bytes.decode("utf-16-le")
    else:
        # Work in Python string space
        doc = template
        for e in evs:
            offset = int(e["offset"])
            old = e.get("oldFragment", "")
            new = e.get("newFragment", "")
            doc = _apply_event_fuzzy_text(doc, offset, old, new, window=window)
        return doc
