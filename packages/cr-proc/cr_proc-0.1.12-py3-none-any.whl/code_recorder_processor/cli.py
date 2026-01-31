"""Command-line interface for code recorder processor."""
import argparse
import glob
import sys
from pathlib import Path
from typing import Any

from .api.build import reconstruct_file_from_events
from .api.document import (
    filter_events_by_document,
    get_recorded_documents,
    resolve_document,
    resolve_template_file,
    find_matching_template,
)
from .api.load import load_jsonl
from .api.output import write_batch_json_output
from .api.verify import (
    check_time_limit,
    combine_time_info,
    compare_submitted_file,
    detect_external_copypaste,
    template_diff,
    verify,
)
from .display import (
    display_submitted_file_comparison,
    display_suspicious_events,
    display_template_diff,
    display_time_info,
    print_batch_header,
    print_batch_summary,
)
from .playback import playback_recording


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser.

    Returns
    -------
    argparse.ArgumentParser
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="Process and verify code recorder JSONL files"
    )
    parser.add_argument(
        "files",
        type=str,
        nargs="+",
        help="Path(s) to JSONL file(s) and optionally a template file. "
        "JSONL files: compressed JSONL file(s) (*.recording.jsonl.gz). "
        "Supports glob patterns like 'recordings/*.jsonl.gz'. "
        "Template file (optional last positional): template file path. "
        "Omit to use --template-dir instead.",
    )
    parser.add_argument(
        "--template-dir",
        type=Path,
        default=None,
        help="Directory containing template files (overrides positional template file). "
        "Will search for files matching the document name. "
        "If no match found, reconstruction proceeds with warning.",
    )
    parser.add_argument(
        "-t",
        "--time-limit",
        type=int,
        default=None,
        help="Maximum allowed time in minutes between first and last edit. "
        "If exceeded, recording is flagged. Applied individually to each recording file.",
    )
    parser.add_argument(
        "-d",
        "--document",
        type=str,
        default=None,
        help="Document path or filename to process from the recording. "
        "Defaults to the document whose extension matches the template file.",
    )
    parser.add_argument(
        "-o",
        "--output-json",
        type=Path,
        default=None,
        help="Path to output JSON file with verification results. "
        "Uses consistent format for both single and batch modes, with batch_mode flag. "
        "In batch mode, includes combined_time_info across all files.",
    )
    parser.add_argument(
        "-f",
        "--output-file",
        type=Path,
        default=None,
        help="Write reconstructed code to specified file instead of stdout. "
        "In batch mode, this should be a directory where files will be named after the input files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory to write reconstructed code files in batch mode (one file per recording). "
        "Files are named based on input recording filenames.",
    )
    parser.add_argument(
        "--submitted-file",
        type=Path,
        default=None,
        help="Path to the submitted final file to verify against the reconstructed output. "
        "If provided, the reconstructed code will be compared to this file.",
    )
    parser.add_argument(
        "--submitted-dir",
        type=Path,
        default=None,
        help="Directory containing submitted files to compare against. "
        "For each recording, the corresponding submitted file will be found by matching the filename. "
        "For example, 'homework0-ISC.recording.jsonl.gz' will match 'homework0-ISC.py' in the directory.",
    )
    parser.add_argument(
        "-s",
        "--show-autocomplete-details",
        action="store_true",
        help="Show individual auto-complete events in addition to "
        "aggregate statistics",
    )
    parser.add_argument(
        "-p",
        "--playback",
        action="store_true",
        help="Play back the recording in real-time, showing code evolution",
    )
    parser.add_argument(
        "--playback-speed",
        type=float,
        default=1.0,
        help="Playback speed multiplier (1.0 = real-time, 2.0 = 2x speed, 0.5 = half speed)",
    )
    return parser


def expand_file_patterns(patterns: list[str]) -> list[Path]:
    """
    Expand glob patterns and validate files exist.

    Parameters
    ----------
    patterns : list[str]
        List of file paths or glob patterns

    Returns
    -------
    list[Path]
        List of existing file paths

    Raises
    ------
    FileNotFoundError
        If no files are found
    """
    jsonl_files = []
    for pattern in patterns:
        expanded = glob.glob(pattern)
        if expanded:
            jsonl_files.extend([Path(f) for f in expanded])
        else:
            # If no glob match, treat as literal path
            jsonl_files.append(Path(pattern))

    if not jsonl_files:
        raise FileNotFoundError("No JSONL files found")

    # Check if files exist
    existing_files = [f for f in jsonl_files if f.exists()]
    if not existing_files:
        raise FileNotFoundError("None of the specified files exist")

    # Warn about missing files
    if len(existing_files) < len(jsonl_files):
        missing = [f for f in jsonl_files if f not in existing_files]
        for f in missing:
            print(f"Warning: File not found: {f}", file=sys.stderr)

    return existing_files


def find_submitted_file(
    jsonl_file: Path,
    submitted_dir: Path,
    target_document: str | None,
) -> Path | None:
    """
    Find the submitted file corresponding to a recording file.

    Matches by replacing '.recording.jsonl.gz' with the extension of the
    target document (or '.py' if not specified).

    Parameters
    ----------
    jsonl_file : Path
        Path to the JSONL recording file
    submitted_dir : Path
        Directory containing submitted files
    target_document : str | None
        Target document path (to extract extension)

    Returns
    -------
    Path | None
        Path to the submitted file if found, None otherwise
    """
    # Determine the file extension from target_document or default to .py
    extension = ".py"
    if target_document:
        extension = Path(target_document).suffix or ".py"

    # Remove '.recording.jsonl.gz' and add the appropriate extension
    base_name = jsonl_file.name.replace(".recording.jsonl.gz", "")
    submitted_filename = base_name + extension

    submitted_file = submitted_dir / submitted_filename
    if submitted_file.exists():
        return submitted_file

    return None


def process_single_file(
    jsonl_path: Path,
    template_data: str,
    target_document: str | None,
    time_limit: int | None,
    submitted_file: Path | None = None,
    submitted_dir: Path | None = None,
) -> tuple[bool, str, list[dict[str, Any]], dict[str, Any] | None, str, tuple[dict[str, Any], ...], dict[str, Any] | None]:
    """
    Process a single JSONL recording file.

    Parameters
    ----------
    jsonl_path : Path
        Path to the JSONL file
    template_data : str
        Template file content
    target_document : str | None
        Document to process
    time_limit : int | None
        Time limit in minutes
    submitted_file : Path | None
        Path to the submitted file to compare against
    submitted_dir : Path | None
        Directory containing submitted files to compare against

    Returns
    -------
    tuple
        (verified, reconstructed_code, suspicious_events, time_info, template_diff_text, doc_events, submitted_comparison)
    """
    try:
        json_data = load_jsonl(jsonl_path)
    except (FileNotFoundError, ValueError, IOError) as e:
        print(f"Error loading {jsonl_path}: {e}", file=sys.stderr)
        return False, "", [], None, "", (), None

    # Filter events for target document
    doc_events = filter_events_by_document(json_data, target_document)
    if target_document and not doc_events:
        print(
            f"Warning: No events found for document '{target_document}' in {jsonl_path}",
            file=sys.stderr,
        )
        return False, "", [], None, "", (), None

    # Check time information
    time_info = check_time_limit(doc_events, time_limit)

    # Verify and process the recording
    try:
        verified_template, suspicious_events = verify(template_data, doc_events)
        reconstructed = reconstruct_file_from_events(
            doc_events, verified_template, document_path=target_document
        )

        # Compare with submitted file if provided
        submitted_comparison = None
        actual_submitted_file = submitted_file

        # If submitted_dir is provided, find the matching file
        if submitted_dir and not submitted_file:
            actual_submitted_file = find_submitted_file(jsonl_path, submitted_dir, target_document)
            if actual_submitted_file:
                print(f"Found submitted file: {actual_submitted_file.name}", file=sys.stderr)

        if actual_submitted_file and actual_submitted_file.exists():
            submitted_comparison = compare_submitted_file(reconstructed, actual_submitted_file)
        elif actual_submitted_file:
            print(f"Warning: Submitted file not found: {actual_submitted_file}", file=sys.stderr)

        return True, reconstructed, suspicious_events, time_info, "", doc_events, submitted_comparison
    except ValueError as e:
        # If verification fails but we have events, still try to reconstruct
        print(f"Warning: Verification failed for {jsonl_path}: {e}", file=sys.stderr)
        try:
            if not doc_events:
                return False, "", [], time_info, "", (), None

            # Compute diff against template and still detect suspicious events
            diff_text = template_diff(template_data, doc_events)
            suspicious_events = detect_external_copypaste(doc_events)

            # Reconstruct using the initial recorded state
            initial_state = doc_events[0].get("newFragment", "")
            reconstructed = reconstruct_file_from_events(
                doc_events, initial_state, document_path=target_document
            )

            # Compare with submitted file if provided
            submitted_comparison = None
            actual_submitted_file = submitted_file

            # If submitted_dir is provided, find the matching file
            if submitted_dir and not submitted_file:
                actual_submitted_file = find_submitted_file(jsonl_path, submitted_dir, target_document)
                if actual_submitted_file:
                    print(f"Found submitted file: {actual_submitted_file.name}", file=sys.stderr)

            if actual_submitted_file and actual_submitted_file.exists():
                submitted_comparison = compare_submitted_file(reconstructed, actual_submitted_file)
            elif actual_submitted_file:
                print(f"Warning: Submitted file not found: {actual_submitted_file}", file=sys.stderr)

            return False, reconstructed, suspicious_events, time_info, diff_text, doc_events, submitted_comparison
        except Exception as reconstruction_error:
            print(
                f"Error reconstructing {jsonl_path}: {type(reconstruction_error).__name__}: {reconstruction_error}",
                file=sys.stderr,
            )
            return False, "", [], time_info, "", (), None
    except Exception as e:
        print(
            f"Error processing {jsonl_path}: {type(e).__name__}: {e}",
            file=sys.stderr,
        )
        return False, "", [], time_info, "", (), None


def write_reconstructed_file(
    output_path: Path,
    content: str,
    file_description: str = "Reconstructed code"
) -> bool:
    """
    Write reconstructed code to a file.

    Parameters
    ----------
    output_path : Path
        Path to write to
    content : str
        Content to write
    file_description : str
        Description for success message

    Returns
    -------
    bool
        True if successful, False otherwise
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content + '\n')
        print(f"{file_description} written to: {output_path}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        return False


def handle_playback_mode(
    jsonl_file: Path,
    template_file: Path,
    template_data: str,
    document_override: str | None,
    speed: float,
) -> int:
    """
    Handle playback mode for a single file.

    Parameters
    ----------
    jsonl_file : Path
        Path to the recording file
    template_file : Path
        Path to the template file
    template_data : str
        Template file content
    document_override : str | None
        Document override
    speed : float
        Playback speed

    Returns
    -------
    int
        Exit code (0 for success, 1 for error)
    """
    try:
        json_data = load_jsonl(jsonl_file)
        recorded_docs = get_recorded_documents(json_data)
        target_document = resolve_document(recorded_docs, template_file, document_override)

        if target_document:
            playback_recording(json_data, target_document, template_data, speed)
            return 0
        else:
            print("Error: No documents found in recording", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"Error loading file for playback: {e}", file=sys.stderr)
        return 1


def process_batch(
    jsonl_files: list[Path],
    template_base: Path | None,
    template_data: str,
    args: argparse.Namespace,
) -> tuple[list[dict[str, Any]], bool]:
    """
    Process multiple recording files in batch mode.

    Parameters
    ----------
    jsonl_files : list[Path]
        List of JSONL files to process
    template_base : Path
        Path to template file or directory
    template_data : str
        Template file content
    args : argparse.Namespace
        Command-line arguments

    Returns
    -------
    tuple
        (results, all_verified)
    """
    results = []
    all_verified = True
    output_dir = args.output_dir or (
        args.output_file if args.output_file and args.output_file.is_dir() else None
    )

    for i, jsonl_file in enumerate(jsonl_files, 1):
        print_batch_header(i, len(jsonl_files), jsonl_file.name)

        # Determine target document for this file
        try:
            file_data = load_jsonl(jsonl_file)
            recorded_docs = get_recorded_documents(file_data)
            target_document = resolve_document(recorded_docs, template_base, args.document)
        except (FileNotFoundError, ValueError, IOError) as e:
            print(f"Error determining document: {e}", file=sys.stderr)
            all_verified = False
            continue

        # If using template directory, find the matching template for this document
        if args.template_dir and target_document:
            matching_template_path = find_matching_template(args.template_dir, target_document)
            if matching_template_path:
                file_template_data = matching_template_path.read_text()
                print(f"Using template: {matching_template_path.name}", file=sys.stderr)
            else:
                file_template_data = ""
                print(
                    f"Warning: No matching template found for {target_document}. "
                    "Reconstruction will proceed without template verification.",
                    file=sys.stderr
                )
        else:
            file_template_data = template_data

        # Process the file
        verified, reconstructed, suspicious_events, time_info, diff_text, doc_events, submitted_comparison = process_single_file(
            jsonl_file, file_template_data, target_document, args.time_limit, args.submitted_file, args.submitted_dir
        )

        if not verified:
            all_verified = False

        # Display results
        display_time_info(time_info)
        display_suspicious_events(suspicious_events, args.show_autocomplete_details)
        display_template_diff(diff_text)
        display_submitted_file_comparison(submitted_comparison)

        # Store results
        results.append({
            "jsonl_file": jsonl_file,
            "target_document": target_document,
            "verified": verified,
            "reconstructed": reconstructed,
            "suspicious_events": suspicious_events,
            "time_info": time_info,
            "template_diff": diff_text,
            "doc_events": doc_events,
            "submitted_comparison": submitted_comparison,
        })

        # Write output file if requested
        if reconstructed and output_dir:
            output_name = jsonl_file.stem.replace(".recording.jsonl", "") + ".py"
            output_path = output_dir / output_name
            write_reconstructed_file(output_path, reconstructed, "Written to")

    return results, all_verified


def process_single(
    jsonl_file: Path,
    template_base: Path | None,
    template_data: str,
    args: argparse.Namespace,
) -> tuple[list[dict[str, Any]], bool]:
    """
    Process a single recording file.

    Parameters
    ----------
    jsonl_file : Path
        Path to JSONL file
    template_base : Path
        Path to template file or directory
    template_data : str
        Template file content
    args : argparse.Namespace
        Command-line arguments

    Returns
    -------
    tuple
        (results, verified)
    """
    try:
        file_data = load_jsonl(jsonl_file)
        recorded_docs = get_recorded_documents(file_data)
        target_document = resolve_document(recorded_docs, template_base, args.document)
    except (FileNotFoundError, ValueError, IOError) as e:
        print(f"Error determining document: {e}", file=sys.stderr)
        return [], False

    # If using template directory, find the matching template for this document
    if args.template_dir and target_document:
        matching_template_path = find_matching_template(args.template_dir, target_document)
        if matching_template_path:
            file_template_data = matching_template_path.read_text()
            print(f"Using template: {matching_template_path.name}", file=sys.stderr)
        else:
            file_template_data = ""
            print(
                f"Warning: No matching template found for {target_document}. "
                "Reconstruction will proceed without template verification.",
                file=sys.stderr
            )
    else:
        file_template_data = template_data

    print(f"Processing: {target_document or template_base}", file=sys.stderr)

    verified, reconstructed, suspicious_events, time_info, diff_text, doc_events, submitted_comparison = process_single_file(
        jsonl_file, file_template_data, target_document, args.time_limit, args.submitted_file, args.submitted_dir
    )

    # Display results
    display_time_info(time_info)
    display_suspicious_events(suspicious_events, args.show_autocomplete_details)
    display_template_diff(diff_text)
    display_submitted_file_comparison(submitted_comparison)

    # Write output file if requested
    if reconstructed and args.output_file:
        if not write_reconstructed_file(args.output_file, reconstructed):
            return [], False

    results = [{
        "jsonl_file": jsonl_file,
        "target_document": target_document,
        "verified": verified,
        "reconstructed": reconstructed,
        "suspicious_events": suspicious_events,
        "time_info": time_info,
        "template_diff": diff_text,
        "doc_events": doc_events,
        "submitted_comparison": submitted_comparison,
    }]

    return results, verified


def main() -> int:
    """
    Main entry point for the CLI application.

    Returns
    -------
    int
        Exit code (0 for success, 1 for errors)
    """
    parser = create_parser()
    args = parser.parse_args()

    # Parse files argument: last one may be template_file if it's not a JSONL file
    files_list = args.files
    template_file = None
    jsonl_patterns = files_list

    # If we have more than one file and the last one doesn't look like a JSONL file,
    # treat it as the template file
    if len(files_list) > 1 and not files_list[-1].endswith(('.jsonl', '.jsonl.gz')):
        template_file = Path(files_list[-1])
        jsonl_patterns = files_list[:-1]

    # Validate that at least one of template_file or template_dir is provided
    if not template_file and not args.template_dir:
        print("Error: Either a template file or --template-dir must be provided", file=sys.stderr)
        parser.print_help()
        return 1

    # Validate that both --submitted-file and --submitted-dir are not provided simultaneously
    if args.submitted_file and args.submitted_dir:
        print("Error: Cannot specify both --submitted-file and --submitted-dir", file=sys.stderr)
        return 1

    # Expand file patterns and validate
    try:
        jsonl_files = expand_file_patterns(jsonl_patterns)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    batch_mode = len(jsonl_files) > 1
    if batch_mode:
        print(f"Processing {len(jsonl_files)} recording files in batch mode", file=sys.stderr)

    # Determine template source (use template_dir if provided, otherwise template_file)
    template_path = args.template_dir if args.template_dir else template_file

    # Handle playback mode (single file only)
    if not batch_mode and args.playback:
        try:
            json_data = load_jsonl(jsonl_files[0])
            recorded_docs = get_recorded_documents(json_data)
            target_document = resolve_document(recorded_docs, template_path, args.document)

            # Get template data for playback
            template_data, _ = resolve_template_file(
                template_file if not args.template_dir else None,
                args.template_dir,
                target_document
            )

            if target_document:
                playback_recording(json_data, target_document, template_data, args.playback_speed)
                return 0
            else:
                print("Error: No documents found in recording", file=sys.stderr)
                return 1
        except Exception as e:
            print(f"Error loading file for playback: {e}", file=sys.stderr)
            return 1

    # Get template data
    try:
        # If using a template directory, skip loading a global template here
        # Let per-file matching handle it in process_batch/process_single
        if args.template_dir:
            template_data = ""
        else:
            template_data, _ = resolve_template_file(
                template_file if not args.template_dir else None,
                None,
                None
            )
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Process files
    if batch_mode:
        results, all_verified = process_batch(
            jsonl_files, template_path, template_data, args
        )
    else:
        results, all_verified = process_single(
            jsonl_files[0], template_path, template_data, args
        )

    if not results:
        return 1

    # Output summary and combined report for batch mode
    if batch_mode:
        failed_files = [r["jsonl_file"].name for r in results if not r["verified"]]
        verified_count = len(results) - len(failed_files)
        print_batch_summary(len(results), verified_count, failed_files)

        # Display combined time report
        all_events = [r["doc_events"] for r in results]
        combined_time = None
        if any(all_events):
            combined_time = combine_time_info(all_events, args.time_limit)
            display_time_info(combined_time, is_combined=True)

        # Write JSON output
        if args.output_json:
            try:
                write_batch_json_output(
                    args.output_json, results, combined_time, all_verified, batch_mode=True
                )
            except Exception as e:
                print(f"Error writing batch JSON output: {e}", file=sys.stderr)
    else:
        # Single file mode - write JSON output
        if args.output_json:
            try:
                write_batch_json_output(
                    args.output_json, results, results[0]["time_info"],
                    results[0]["verified"], batch_mode=False
                )
            except Exception as e:
                print(f"Error writing JSON output: {e}", file=sys.stderr)

    return 0 if all_verified else 1


if __name__ == "__main__":
    sys.exit(main())
