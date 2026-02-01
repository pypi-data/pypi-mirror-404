#!/usr/bin/env python3
"""Aegis SDK Command Line Interface.

A CLI tool for detecting and masking PII in text and files.

Usage:
    aegis scan "text to scan"
    aegis mask "text to mask"
    aegis process input.txt -o output.txt
    aegis check-license
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from aegis_sdk import (
    Aegis,
    StreamingProcessor,
    CSVStreamProcessor,
    Decision,
)


def check_for_updates(current_version: str) -> Optional[str]:
    """Check PyPI for newer version. Returns latest version if update available, None otherwise."""
    try:
        import urllib.request
        import urllib.error

        url = "https://pypi.org/pypi/aegis-sdk/json"
        request = urllib.request.Request(url, headers={"User-Agent": "aegis-sdk"})

        with urllib.request.urlopen(request, timeout=3) as response:
            data = json.loads(response.read().decode())
            latest = data.get("info", {}).get("version", "")

            if latest and latest != current_version:
                # Simple version comparison (works for semantic versioning)
                current_parts = [int(x) for x in current_version.split(".")]
                latest_parts = [int(x) for x in latest.split(".")]

                if latest_parts > current_parts:
                    return latest
    except Exception:
        pass  # Silently fail - don't interrupt user workflow

    return None


def cmd_scan(args):
    """Scan text for PII."""
    aegis = Aegis(include_samples=not args.no_samples)

    if args.file:
        with open(args.file, "r") as f:
            text = f.read()
    else:
        text = args.text

    detected = aegis.detect(text)

    if args.json:
        output = {
            "detected": [
                {
                    "type": d.type,
                    "count": d.count,
                    "sample": d.sample if d.sample else None
                }
                for d in detected
            ],
            "has_pii": len(detected) > 0
        }
        print(json.dumps(output, indent=2))
    else:
        if not detected:
            print("No PII detected.")
        else:
            print(f"Detected {len(detected)} type(s) of sensitive data:\n")
            for item in detected:
                sample = f" (sample: {item.sample})" if item.sample else ""
                print(f"  - {item.type}: {item.count} occurrence(s){sample}")

    return 0 if not detected else 1


def cmd_mask(args):
    """Mask PII in text."""
    aegis = Aegis()

    if args.file:
        with open(args.file, "r") as f:
            text = f.read()
    else:
        text = args.text

    masked = aegis.mask(text)

    if args.output:
        with open(args.output, "w") as f:
            f.write(masked)
        print(f"Masked output written to {args.output}")
    else:
        print(masked)

    return 0


def cmd_process(args):
    """Process text with full decision logic."""
    aegis = Aegis(include_samples=not args.no_samples)

    if args.file:
        with open(args.file, "r") as f:
            text = f.read()
    else:
        text = args.text

    result = aegis.process(text, destination=args.destination)

    if args.json:
        output = {
            "decision": str(result.decision.value) if hasattr(result.decision, 'value') else str(result.decision),
            "summary": result.summary,
            "detected": [
                {"type": d.type, "count": d.count}
                for d in result.detected
            ],
            "masked_content": result.masked_content,
            "is_blocked": result.is_blocked,
            "bytes_processed": result.bytes_processed
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"Decision: {result.decision}")
        print(f"Summary: {result.summary}")

        if result.detected:
            print(f"\nDetected:")
            for item in result.detected:
                print(f"  - {item.type}: {item.count}")

        if result.masked_content and not result.is_blocked:
            print(f"\nMasked content:")
            print(result.masked_content)

        if result.suggested_fix:
            print(f"\nSuggested fix: {result.suggested_fix}")

    if args.output and result.masked_content:
        with open(args.output, "w") as f:
            f.write(result.masked_content)
        print(f"\nOutput written to {args.output}")

    return 0 if not result.is_blocked else 1


def cmd_process_file(args):
    """Process a file with streaming."""
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        return 1

    output_path = Path(args.output) if args.output else None

    # Determine processor based on file type
    if input_path.suffix.lower() == ".csv":
        processor = CSVStreamProcessor()
        result = processor.process(
            input_path=input_path,
            output_path=output_path,
            destination=args.destination,
            has_header=not args.no_header
        )
    else:
        processor = StreamingProcessor(chunk_size_mb=args.chunk_mb or 10)

        def progress_callback(bytes_processed, total_bytes, chunks):
            if not args.quiet:
                mb = bytes_processed / (1024 * 1024)
                print(f"\rProcessed: {mb:.1f} MB", end="", file=sys.stderr)

        result = processor.process_file(
            input_path=input_path,
            output_path=output_path,
            destination=args.destination,
            on_progress=progress_callback if not args.quiet else None,
            stop_on_block=args.stop_on_block
        )

        if not args.quiet:
            print(file=sys.stderr)  # New line after progress

    if args.json:
        output = {
            "decision": str(result.decision.value) if hasattr(result.decision, 'value') else str(result.decision),
            "summary": result.summary,
            "bytes_processed": result.bytes_processed,
            "chunks_processed": result.chunks_processed,
            "detected": [
                {"type": d.type, "count": d.count}
                for d in result.detected
            ],
            "output_path": str(output_path) if output_path else None,
            "blocked_early": result.blocked_early
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"Decision: {result.decision}")
        print(f"Summary: {result.summary}")
        print(f"Processed: {result.mb_processed:.2f} MB in {result.chunks_processed} chunks")

        if result.detected:
            print(f"\nDetected:")
            for item in result.detected:
                print(f"  - {item.type}: {item.count}")

        if output_path:
            print(f"\nOutput: {output_path}")

        if result.blocked_early:
            print("\nNote: Processing stopped early due to blocked content")

    return 0 if result.decision != Decision.BLOCKED else 1


def cmd_check_license(args):
    """Check license status."""
    from aegis_sdk import LicenseManager, LicenseValidationError

    if not args.license_key:
        print("Error: License key required. Use --license-key or AEGIS_LICENSE_KEY env var", file=sys.stderr)
        return 1

    manager = LicenseManager(
        license_key=args.license_key,
        offline_mode=args.offline
    )

    try:
        info = manager.validate()

        if args.json:
            output = {
                "valid": info.valid,
                "org_id": info.org_id,
                "expires": info.expires,
                "policy_version": info.policy_version
            }
            print(json.dumps(output, indent=2))
        else:
            print(f"License Status: {'Valid' if info.valid else 'Invalid'}")
            print(f"Organization: {info.org_id}")
            print(f"Expires: {info.expires}")
            print(f"Policy Version: {info.policy_version}")

        return 0 if info.valid else 1

    except LicenseValidationError as e:
        if args.json:
            print(json.dumps({"valid": False, "error": str(e)}))
        else:
            print(f"License validation failed: {e}", file=sys.stderr)
        return 1


def cmd_version(args):
    """Show version and check for updates."""
    from aegis_sdk import __version__

    print(f"aegis-sdk {__version__}")

    # Check for updates (non-blocking, fails silently)
    latest = check_for_updates(__version__)
    if latest:
        print(f"\nUpdate available: {latest}")
        print("Run 'pip install --upgrade aegis-sdk' to update")

    return 0


def main():
    """Main entry point for CLI."""
    import os

    parser = argparse.ArgumentParser(
        prog="aegis",
        description="Aegis SDK - PII detection and masking for AI applications"
    )
    from aegis_sdk import __version__
    parser.add_argument("--version", "-v", action="store_true", help="Show version and check for updates")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # scan command
    scan_parser = subparsers.add_parser("scan", help="Scan text for PII")
    scan_parser.add_argument("text", nargs="?", help="Text to scan")
    scan_parser.add_argument("-f", "--file", help="File to scan")
    scan_parser.add_argument("--no-samples", action="store_true", help="Don't include samples")
    scan_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # mask command
    mask_parser = subparsers.add_parser("mask", help="Mask PII in text")
    mask_parser.add_argument("text", nargs="?", help="Text to mask")
    mask_parser.add_argument("-f", "--file", help="File to mask")
    mask_parser.add_argument("-o", "--output", help="Output file")

    # process command
    process_parser = subparsers.add_parser("process", help="Process text with decision logic")
    process_parser.add_argument("text", nargs="?", help="Text to process")
    process_parser.add_argument("-f", "--file", help="File to process")
    process_parser.add_argument("-o", "--output", help="Output file")
    process_parser.add_argument("-d", "--destination", default="AI_TOOL",
                                choices=["AI_TOOL", "VENDOR", "CUSTOMER"],
                                help="Target destination")
    process_parser.add_argument("--no-samples", action="store_true", help="Don't include samples")
    process_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # process-file command (streaming)
    file_parser = subparsers.add_parser("process-file", help="Process file with streaming")
    file_parser.add_argument("input", help="Input file path")
    file_parser.add_argument("-o", "--output", help="Output file path")
    file_parser.add_argument("-d", "--destination", default="AI_TOOL",
                             choices=["AI_TOOL", "VENDOR", "CUSTOMER"],
                             help="Target destination")
    file_parser.add_argument("--chunk-mb", type=float, help="Chunk size in MB (for text files)")
    file_parser.add_argument("--chunk-rows", type=int, help="Chunk size in rows (for CSV files)")
    file_parser.add_argument("--no-header", action="store_true", help="CSV has no header row")
    file_parser.add_argument("--stop-on-block", action="store_true", help="Stop processing if blocked")
    file_parser.add_argument("-q", "--quiet", action="store_true", help="Suppress progress output")
    file_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # check-license command
    license_parser = subparsers.add_parser("check-license", help="Check license status")
    license_parser.add_argument("--license-key", default=os.environ.get("AEGIS_LICENSE_KEY"),
                                help="License key (or use AEGIS_LICENSE_KEY env var)")
    license_parser.add_argument("--offline", action="store_true", help="Offline mode")
    license_parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    # Handle --version flag
    if args.version:
        return cmd_version(args)

    if not args.command:
        parser.print_help()
        return 0

    # Dispatch to command handler
    commands = {
        "scan": cmd_scan,
        "mask": cmd_mask,
        "process": cmd_process,
        "process-file": cmd_process_file,
        "check-license": cmd_check_license,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
