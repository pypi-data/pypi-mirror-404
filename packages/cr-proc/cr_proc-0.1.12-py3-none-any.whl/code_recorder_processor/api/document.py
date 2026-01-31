"""Document resolution and filtering utilities."""
import difflib
import sys
from pathlib import Path, PureWindowsPath, PurePosixPath
from typing import Any


def normalize_path_string(path_str: str) -> str:
    """
    Normalize a path string to use forward slashes (POSIX style).

    Handles both Windows-style (backslash) and Unix-style (forward slash) paths
    regardless of the current platform. Useful for cross-platform consistency
    when files are created on Windows but processed on other systems.

    Parameters
    ----------
    path_str : str
        Path string (may use Windows or Unix separators)

    Returns
    -------
    str
        Normalized path string using forward slashes
    """
    # Try to detect if this is a Windows path (contains backslashes)
    if "\\" in path_str:
        # Windows-style path
        path_obj = PureWindowsPath(path_str)
    else:
        # Unix-style path (or just a filename)
        path_obj = PurePosixPath(path_str)

    return path_obj.as_posix()


def _normalize_document_path(doc_path: str) -> tuple[str, str]:
    """
    Extract filename and stem from a document path.

    Handles both Windows-style (backslash) and Unix-style (forward slash) paths
    regardless of the current platform.

    Parameters
    ----------
    doc_path : str
        Document path string (may use Windows or Unix separators)

    Returns
    -------
    tuple[str, str]
        (filename, stem) extracted from the path
    """
    # Normalize to forward slashes first, then parse
    normalized = normalize_path_string(doc_path)
    path_obj = PurePosixPath(normalized)
    return path_obj.name, path_obj.stem


def find_matching_template(
    template_dir: Path, document_path: str
) -> Path | None:
    """
    Find a template file that matches or closely matches the document path.

    Searches for template files in the given directory that either:
    1. Exactly match the document filename
    2. Have the same base name (stem) as the document
    3. Have a fuzzy match with the document name

    Parameters
    ----------
    template_dir : Path
        Directory containing template files
    document_path : str
        Path of the document to find a template for

    Returns
    -------
    Path | None
        Path to the matching template file, or None if no good match found
    """
    if not template_dir.is_dir():
        return None

    doc_name, doc_stem = _normalize_document_path(document_path)

    # First, try exact filename match
    exact_match = template_dir / doc_name
    if exact_match.exists() and exact_match.is_file():
        return exact_match

    # Get all template files
    template_files = list(template_dir.glob("*"))
    template_files = [f for f in template_files if f.is_file()]

    if not template_files:
        return None

    # Then try matching by stem (name without extension)
    stem_matches = [f for f in template_files if f.stem == doc_stem]
    if stem_matches:
        return stem_matches[0]

    # Try matching by just the stem component from document (in case doc has extra prefixes/suffixes)
    # For example: "cs111-homework0-CPT.py" -> stem is "cs111-homework0-CPT", but we want to match "cs111-homework0.py"
    # So try matching just the core part before any suffixes like -CPT, -CPY, etc
    for sep in ['-', '_']:
        if sep in doc_stem:
            base_stem = doc_stem.split(sep)[0]
            base_matches = [f for f in template_files if f.stem == base_stem or f.stem.startswith(base_stem + sep)]
            if base_matches:
                return base_matches[0]

    # Finally, try to find the closest match using sequence matching with lower threshold
    matches = difflib.get_close_matches(doc_name, [f.name for f in template_files], n=1, cutoff=0.4)
    if matches:
        return template_dir / matches[0]

    # Last resort: try fuzzy matching on stem
    matches = difflib.get_close_matches(doc_stem, [f.stem for f in template_files], n=1, cutoff=0.4)
    if matches:
        stem_match_files = [f for f in template_files if f.stem == matches[0]]
        if stem_match_files:
            return stem_match_files[0]

    return None


def get_normalized_document_key(doc_path: str) -> tuple[str, str]:
    """
    Get a normalized key for a document based on filename and extension.

    This helps identify documents that are the same but with different paths.
    Handles both Windows and Unix style paths correctly.

    Parameters
    ----------
    doc_path : str
        Document path (may use Windows or Unix separators)

    Returns
    -------
    tuple[str, str]
        (filename_with_extension, extension) for grouping similar documents
    """
    filename, _ = _normalize_document_path(doc_path)
    # Get extension from filename
    if '.' in filename:
        extension = '.' + filename.rsplit('.', 1)[1]
    else:
        extension = ''
    return (filename, extension)


def group_documents_by_name(docs: list[str]) -> dict[tuple[str, str], list[str]]:
    """
    Group documents by their normalized key (name + extension).

    Documents with the same filename and extension but different paths
    are considered the same file (likely renamed).

    Parameters
    ----------
    docs : list[str]
        List of document paths from recording

    Returns
    -------
    dict[tuple[str, str], list[str]]
        Dictionary mapping (filename, extension) to list of paths with that name
    """
    groups = {}
    for doc in docs:
        key = get_normalized_document_key(doc)
        if key not in groups:
            groups[key] = []
        groups[key].append(doc)
    return groups


def get_recorded_documents(events: tuple[dict[str, Any], ...]) -> list[str]:
    """
    Extract unique document paths from recording events.

    Parameters
    ----------
    events : tuple[dict[str, Any], ...]
        Recording events loaded from JSONL

    Returns
    -------
    list[str]
        Sorted list of unique document paths
    """
    documents = {
        e.get("document")
        for e in events
        if "document" in e and e.get("document") is not None
    }
    return sorted([d for d in documents if d is not None])


def filter_events_by_document(
    events: tuple[dict[str, Any], ...], document: str | None
) -> tuple[dict[str, Any], ...]:
    """
    Filter events to only those for a specific document.

    Parameters
    ----------
    events : tuple[dict[str, Any], ...]
        All recording events
    document : str | None
        Document path to filter by, or None to return all events

    Returns
    -------
    tuple[dict[str, Any], ...]
        Filtered events
    """
    if document:
        return tuple(e for e in events if e.get("document") == document)
    return events


def resolve_document(
    docs: list[str], template_path: Path | None, override: str | None
) -> str | None:
    """
    Determine which document from the recording to process.

    Handles deduplication of documents with same name/extension (treating them as renames).

    Parameters
    ----------
    docs : list[str]
        List of document paths found in the recording
    template_path : Path | None
        Path to template file or directory (used for extension matching if it's a file)
    override : str | None
        Explicit document name or path override

    Returns
    -------
    str | None
        The resolved document path, or None if no documents exist

    Raises
    ------
    ValueError
        If document resolution is ambiguous or the override doesn't match
    """
    if not docs:
        return None

    # Group documents by name/extension to handle renames
    doc_groups = group_documents_by_name(docs)

    # For ambiguity checking, use the groups (deduplicated by name)
    unique_docs = [paths[0] for paths in doc_groups.values()]

    if override:
        matches = [
            d for d in unique_docs
            if d.endswith(override) or _normalize_document_path(d)[0] == override
        ]
        if not matches:
            raise ValueError(
                f"No document in recording matches '{override}'. Available: {unique_docs}"
            )
        if len(matches) > 1:
            raise ValueError(
                f"Ambiguous document override '{override}'. Matches: {matches}"
            )
        return matches[0]

    # If template_path is provided and is a file (not directory), use its extension for matching
    if template_path and template_path.is_file():
        template_ext = template_path.suffix
        ext_matches = [
            d for d in unique_docs
            if _normalize_document_path(d)[0].endswith(template_ext)
        ]
        if len(ext_matches) == 1:
            return ext_matches[0]
        if len(ext_matches) > 1:
            raise ValueError(
                f"Multiple documents share extension '{template_ext}': {ext_matches}. "
                "Use --document to choose one."
            )

    if len(unique_docs) == 1:
        return unique_docs[0]

    raise ValueError(
        "Could not determine document to process. Use --document to select one. "
        f"Available documents: {unique_docs}"
    )


def resolve_template_file(
    template_path: Path | None,
    template_dir: Path | None,
    document_path: str | None
) -> tuple[str, bool]:
    """
    Resolve which template file to use and whether a warning was issued.

    Supports both a direct template file path or a directory to search for templates.
    If using a directory and no exact match is found, a warning is issued but
    reconstruction will still proceed.

    Parameters
    ----------
    template_path : Path | None
        Direct path to a template file (if provided)
    template_dir : Path | None
        Directory to search for template files (if provided)
    document_path : str | None
        Path of the document being processed (for matching)

    Returns
    -------
    tuple[str, bool]
        (template_content, had_warning) where had_warning indicates if template was not found
        but reconstruction is proceeding anyway

    Raises
    ------
    FileNotFoundError
        If a direct template path is specified but not found
    ValueError
        If neither template_path nor template_dir is provided
    """
    if template_path is not None:
        # Direct template file path provided
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")
        return template_path.read_text(), False

    if template_dir is not None:
        # Search for template in directory
        if not template_dir.is_dir():
            raise ValueError(f"Template directory does not exist: {template_dir}")

        # Find a matching template
        if document_path:
            matching_template = find_matching_template(template_dir, document_path)
            if matching_template:
                return matching_template.read_text(), False

        # No matching template found, issue warning
        print(
            f"Warning: No matching template found in {template_dir}. "
            "Reconstruction will proceed, but checks may fail.",
            file=sys.stderr
        )
        return "", True  # Empty template, but continue

    raise ValueError("Either template_path or template_dir must be provided")
