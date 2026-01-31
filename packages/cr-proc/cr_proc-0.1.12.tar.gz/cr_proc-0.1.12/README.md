# `code_recorder_processor`

[![CI](https://github.com/BYU-CS-Course-Ops/code_recorder_processor/actions/workflows/ci.yml/badge.svg)](https://github.com/BYU-CS-Course-Ops/code_recorder_processor/actions/workflows/ci.yml)

This contains code to process and verify the `*.recorder.jsonl.gz` files that
are produced by the
[jetbrains-recorder](https://github.com/BYU-CS-Course-Ops/jetbrains-recorder).

## Installation

Install the package and its dependencies using Poetry:

```bash
poetry install
```

## Usage

The processor can be run using the `cr_proc` command with recording file(s) and
a template:

```bash
poetry run cr_proc <path-to-jsonl-file> <path-to-template-file>
```

### Batch Processing

You can process multiple recording files at once (e.g., for different students'
submissions):

```bash
# Process multiple files
poetry run cr_proc file1.jsonl.gz file2.jsonl.gz template.py

# Using glob patterns
poetry run cr_proc recordings/*.jsonl.gz template.py
```

When processing multiple files:

- Each recording is processed independently (for different students/documents)
- Time calculations and verification are done separately for each file
- A combined time report is shown at the end summarizing total editing time
  across all recordings
- Results can be output to individual files using `--output-dir`

### Arguments

- `<path-to-jsonl-file>`: Path(s) to compressed JSONL file(s)
  (`*.recorder.jsonl.gz`) produced by the jetbrains-recorder. Supports multiple
  files and glob patterns like `recordings/*.jsonl.gz`
- `<path-to-template-file>`: Path to the initial template file that was recorded

### Options

- `-t, --time-limit MINUTES`: (Optional) Maximum allowed time in minutes between
  the first and last edit in the recording. Applied individually to each
  recording file and also to the combined total in batch mode. If the elapsed
  time exceeds this limit, the recording is flagged as suspicious.
- `-d, --document DOCUMENT`: (Optional) Document path or filename to process
  from the recording. Defaults to the document whose extension matches the
  template file.
- `-o, --output-json OUTPUT_JSON`: (Optional) Path to output JSON file with
  verification results (time info and suspicious events). In batch mode, creates
  a single JSON file containing all recordings plus the combined time report.
- `-f, --output-file OUTPUT_FILE`: (Optional) Write reconstructed code to
  specified file instead of stdout. For single files only.
- `--output-dir OUTPUT_DIR`: (Optional) Directory to write reconstructed code
  files in batch mode. Files are named based on input recording filenames.
- `--submitted-file SUBMITTED_FILE`: (Optional) Path to the submitted final file
  to verify against the reconstructed output. If provided, the reconstructed code
  will be compared to this file and differences will be reported.
- `--submitted-dir SUBMITTED_DIR`: (Optional) Directory containing submitted files
  to verify against the reconstructed output. For each recording file, the
  corresponding submitted file will be found by matching the filename
  (e.g., `homework0-ISC.recording.jsonl.gz` will match `homework0-ISC.py`).
  Cannot be used with `--submitted-file`.
- `-s, --show-autocomplete-details`: (Optional) Show individual auto-complete
  events in addition to aggregate statistics.
- `-p, --playback`: (Optional) Play back the recording in real-time, showing
  code evolution.
- `--playback-speed SPEED`: (Optional) Playback speed multiplier (1.0 =
  real-time, 2.0 = 2x speed, 0.5 = half speed).

### Examples

Basic usage:

```bash
poetry run cr_proc homework0.recording.jsonl.gz homework0.py
```

With time limit flag:

```bash
poetry run cr_proc homework0.recording.jsonl.gz homework0.py --time-limit 30
```

Batch processing with output directory:

```bash
poetry run cr_proc recordings/*.jsonl.gz template.py --output-dir output/
```

Save JSON results:

```bash
poetry run cr_proc student1.jsonl.gz student2.jsonl.gz template.py -o results/
```

Verify against a single submitted file:

```bash
poetry run cr_proc homework0.recording.jsonl.gz homework0.py --submitted-file submitted_homework0.py
```

Verify against submitted files in a directory (batch mode):

```bash
poetry run cr_proc recordings/*.jsonl.gz template.py --submitted-dir submissions/
```

This will process each recording independently and flag any that exceed 30
minutes.

The processor will:

1. Load the recorded events from the JSONL file
2. Verify that the initial event matches the template (allowances for newline
   differences are made)
3. Reconstruct the final file state by applying all recorded events
4. Output the reconstructed file contents to stdout

### Output

Reconstructed code files are written to disk using `-f/--output-file` (single
file) or `--output-dir` (batch mode). The processor does not output
reconstructed code to stdout.

Verification information, warnings, and errors are printed to stderr, including:

- The document path being processed
- Time information (elapsed time, time span) for each recording
- Suspicious copy-paste and AI activity indicators for each file
- Batch summary showing:
  - Verification status of all processed files
  - Combined time report (total editing time across all recordings)
  - Time limit violations if applicable

### Suspicious Activity Detection

The processor automatically detects and reports three types of suspicious
activity patterns:

#### 1. Time Limit Exceeded

When the `--time-limit` flag is specified, the processor flags recordings where
the elapsed time between the first and last edit exceeds the specified limit.
This can indicate unusually long work sessions or potential external assistance.

Each recording file is checked independently against the time limit. In batch
mode, the combined total time is also checked against the limit.

**Example warning (single file):**

```
Elapsed editing time: 45.5 minutes
Time span (first to last edit): 62.30 minutes

Time limit exceeded!
  Limit: 30 minutes
  First edit: 2025-01-15T10:00:00+00:00
  Last edit: 2025-01-15T11:02:18+00:00
```

**Example warning (batch mode combined report):**

```
================================================================================
BATCH SUMMARY: Processed 3 files
================================================================================
Verified: 3/3

COMBINED TIME REPORT (3 recordings):
Total elapsed editing time: 65.5 minutes
Overall time span: 120.45 minutes

Time limit exceeded!
  Limit: 60 minutes
```

#### 2. External Copy-Paste (Multi-line Pastes)

The processor flags multi-line additions (more than one line) that do not appear
to be copied from within the document itself. These indicate content pasted from
external sources.

**Example warning:**

```
Event #15 (multi-line external paste): 5 lines, 156 chars - newFragment: def helper_function():...
```

#### 3. Rapid One-line Pastes (AI Indicator)

When 3 or more single-line pastes occur within a 1-second window, this is
flagged as a potential AI activity indicator. Human typing does not typically
produce this pattern; rapid sequential pastes suggest automated code generation.

**Example warning:**

```
Events #42-#44 (rapid one-line pastes (AI indicator)): 3 lines, 89 chars
```

### JSON Output Format

The `--output-json` flag generates JSON files with verification results using a
consistent format for both single file and batch modes, making it easier for
tooling to consume.

#### JSON Structure

All JSON output follows this unified format:

- `batch_mode`: Boolean indicating if multiple files were processed
- `total_files`: Number of files processed
- `verified_count`: How many files passed verification
- `all_verified`: Whether all files passed
- `combined_time_info`: Time information (present in both modes):
  - Single file: Contains time info for that file
  - Batch mode: Contains combined time report with:
    - `minutes_elapsed`: Total editing time across all recordings
    - `overall_span_minutes`: Time span from first to last edit
    - `file_count`: Number of recordings
    - `exceeds_limit`: Whether combined time exceeds the limit
- `files`: Array of individual results for each recording

**Single file example:**

```json
{
  "batch_mode": false,
  "total_files": 1,
  "verified_count": 1,
  "all_verified": true,
  "combined_time_info": {
    "minutes_elapsed": 15.74,
    "first_timestamp": "2026-01-15T01:21:35.360168Z",
    "exceeds_limit": false
  },
  "files": [
    {
      "jsonl_file": "recording.jsonl.gz",
      "document": "/path/to/homework.py",
      "verified": true,
      "time_info": { ... },
      "suspicious_events": [ ... ],
      "reconstructed_code": "..."
    }
  ]
}
```

**Batch file example:**

```json
{
  "batch_mode": true,
  "total_files": 2,
  "verified_count": 2,
  "all_verified": true,
  "combined_time_info": {
    "minutes_elapsed": 31.24,
    "overall_span_minutes": 18739.29,
    "file_count": 2,
    "exceeds_limit": false
  },
  "files": [ /* individual results for each file */ ]
}
```

### Error Handling

If verification fails (the recorded initial state doesn't match the template),
the processor will:

- Print an error message to stderr
- Display a diff showing the differences
- Exit with status code 1

If file loading or processing errors occur, the processor will:

- Print a descriptive error message to stderr
- Exit with status code 1

## Future Ideas

- Check for odd typing behavior
