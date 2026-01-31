import jsonl
import zlib
from gzip import BadGzipFile, open as gzip_open
from io import StringIO
from pathlib import Path
from typing import Any


def load_jsonl(file: Path) -> tuple[dict[str, Any], ...]:
    """
    Load JSONL data from a file (gzip compressed or plain text).

    Parameters
    ----------
    file : Path
        Path to the JSONL file (can be .jsonl or .jsonl.gz)

    Returns
    -------
    tuple[dict[str, Any], ...]
        Tuple of dictionaries parsed from the JSONL file

    Raises
    ------
    FileNotFoundError
        If the file does not exist
    IOError
        If there's an error reading the file
    ValueError
        If the file contains invalid JSONL data
    """
    if not file.exists():
        raise FileNotFoundError(f"File not found: {file}")

    if not file.is_file():
        raise ValueError(f"Path is not a file: {file}")

    def _load_jsonl(source: Any) -> tuple[dict[str, Any], ...]:
        return tuple(jsonl.load(source))

    def _read_magic(path: Path) -> bytes:
        try:
            with path.open("rb") as fh:
                return fh.read(2)
        except FileNotFoundError:
            raise
        except OSError:
            return b""

    try:
        data = _load_jsonl(file)
    except BadGzipFile:
        magic = _read_magic(file)
        looks_gzip = magic == b"\x1f\x8b"

        # If it looks like gzip, try an explicit gzip open before giving up.
        if looks_gzip:
            try:
                with gzip_open(file, "rt", encoding="utf-8") as gz:
                    data = _load_jsonl(gz)
            except (BadGzipFile, OSError):
                data = None
        else:
            data = None

        if data is None:
            # If gzip stream is broken, attempt a lenient zlib decompress to salvage content.
            # Handle multiple concatenated gzip streams (common in recordings)
            try:
                raw = file.read_bytes()
                all_text = ""
                remaining = raw

                # Decompress all concatenated gzip streams
                while remaining:
                    dobj = zlib.decompressobj(16 + zlib.MAX_WBITS)
                    try:
                        text_bytes = dobj.decompress(remaining) + dobj.flush()
                        all_text += text_bytes.decode("utf-8", errors="replace")
                        remaining = dobj.unused_data
                        if not text_bytes or not remaining:
                            break
                    except Exception:
                        # If decompression fails, try to salvage what we have
                        break

                if all_text:
                    data = _load_jsonl(StringIO(all_text))
                else:
                    data = None
            except Exception:
                data = None

        if data is None:
            # Fall back to plain text even if the header hinted gzip.
            try:
                with file.open("r", encoding="utf-8", errors="replace") as plain_file:
                    data = _load_jsonl(plain_file)
            except FileNotFoundError as e:
                raise FileNotFoundError(f"Error reading file {file}: {e}")
            except ValueError as e:
                raise ValueError(f"Invalid JSONL format in {file} (plain read fallback): {e}")
            except Exception as e:
                raise IOError(
                    f"Error loading JSONL file {file} without compression (magic={magic!r}): {type(e).__name__}: {e}"
                )
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Error reading file {file}: {e}")
    except ValueError as e:
        raise ValueError(f"Invalid JSONL format in {file}: {e}")
    except Exception as e:
        raise IOError(f"Error loading JSONL file {file}: {type(e).__name__}: {e}")

    if not data:
        raise ValueError(f"JSONL file is empty: {file}")

    return data


def is_edit_event(event: dict[str, Any]) -> bool:
    """
    Check if an event is an edit event (backwards compatible).

    Events are considered edit events if:
    - They have type="edit", OR
    - They don't have a "type" field (legacy/backwards compatibility)

    Parameters
    ----------
    event : dict[str, Any]
        Event dictionary from JSONL

    Returns
    -------
    bool
        True if the event should be processed as an edit event
    """
    event_type = event.get("type")
    # If no type field exists (old format), treat as edit event for backwards compatibility
    # If type field exists, only process if it's "edit"
    return event_type is None or event_type == "edit"


def filter_edit_events(events: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    """
    Filter events to only include edit events (backwards compatible).

    Parameters
    ----------
    events : tuple[dict[str, Any], ...]
        All events from JSONL

    Returns
    -------
    tuple[dict[str, Any], ...]
        Only edit events
    """
    return tuple(e for e in events if is_edit_event(e))


def get_focus_events(events: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    """
    Extract focus status events from recording.

    Parameters
    ----------
    events : tuple[dict[str, Any], ...]
        All events from JSONL

    Returns
    -------
    tuple[dict[str, Any], ...]
        Only focusStatus events with timestamp and focused fields
    """
    return tuple(e for e in events if e.get("type") == "focusStatus")
