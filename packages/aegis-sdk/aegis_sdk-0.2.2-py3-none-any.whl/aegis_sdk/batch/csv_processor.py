"""CSV-specific streaming processor.

This module provides optimized CSV processing that handles
large CSV files row by row with proper parsing and masking.
"""

import csv
import io
from pathlib import Path
from typing import Callable, Iterator, Optional, Union

from aegis_sdk.types import (
    Decision,
    DetectedItem,
    BatchProcessingResult,
)
from aegis_sdk.core.detector import PatternDetector
from aegis_sdk.core.masker import mask_text
from aegis_sdk.core.policy import PolicyEngine


def _csv_row_iterator(
    file_path: Path,
    has_header: bool = True,
) -> Iterator[tuple[list[str], bool]]:
    """Iterate over CSV rows.

    Args:
        file_path: Path to CSV file
        has_header: Whether first row is header

    Yields:
        Tuple of (row_data, is_header)
    """
    with open(file_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            yield row, (i == 0 and has_header)


def _merge_detected_items(items_list: list[list[DetectedItem]]) -> list[DetectedItem]:
    """Merge detected items from multiple rows."""
    type_counts: dict[str, int] = {}
    type_samples: dict[str, Optional[str]] = {}

    for items in items_list:
        for item in items:
            if item.type not in type_counts:
                type_counts[item.type] = 0
                type_samples[item.type] = item.sample
            type_counts[item.type] += item.count

    return [
        DetectedItem(type=t, count=c, sample=type_samples[t])
        for t, c in type_counts.items()
    ]


def process_csv_file(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    destination: str = "AI_TOOL",
    has_header: bool = True,
    columns_to_mask: Optional[list[int]] = None,
    policy_config: Optional[dict] = None,
    include_samples: bool = True,
    on_progress: Optional[Callable[[int, int], None]] = None,
    stop_on_block: bool = False,
) -> BatchProcessingResult:
    """Process a CSV file row by row with streaming.

    This function processes CSV files efficiently by reading row by row,
    detecting and masking sensitive data in each cell.

    Args:
        input_path: Path to input CSV file
        output_path: Optional path for masked output CSV
        destination: Target destination for policy evaluation
        has_header: Whether first row is header (preserved as-is or masked)
        columns_to_mask: Optional list of column indices to mask (all if None)
        policy_config: Optional custom policy configuration
        include_samples: Whether to include masked samples
        on_progress: Optional callback(rows_processed, bytes_processed)
        stop_on_block: Stop processing immediately if blocked

    Returns:
        BatchProcessingResult with processing results

    Example:
        result = process_csv_file(
            "customer_data.csv",
            "masked_data.csv",
            destination="VENDOR",
            columns_to_mask=[1, 2, 3],  # Only mask these columns
            on_progress=lambda r, b: print(f"Processed {r} rows")
        )
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    detector = PatternDetector(include_samples=include_samples)
    policy = PolicyEngine(policy_config)

    all_detected: list[list[DetectedItem]] = []
    bytes_processed = 0
    rows_processed = 0
    blocked_early = False
    actual_output_path: Optional[str] = None

    # Open output file for incremental writing (if provided)
    output_file = None
    output_writer = None
    if output_path:
        output_path = Path(output_path)
        output_file = open(output_path, "w", encoding="utf-8", newline="")
        output_writer = csv.writer(output_file)

    try:
        with open(input_path, "r", encoding="utf-8", newline="") as infile:
            reader = csv.reader(infile)

            for row_idx, row in enumerate(reader):
                is_header = (row_idx == 0 and has_header)

                # Process each cell
                row_detections: list[DetectedItem] = []
                masked_row: list[str] = []

                for col_idx, cell in enumerate(row):
                    # Skip header row or columns not in mask list
                    should_mask = not is_header and (
                        columns_to_mask is None or col_idx in columns_to_mask
                    )

                    if should_mask and cell:
                        # Detect in cell
                        detected = detector.detect(cell)
                        row_detections.extend(detected)

                        # Mask cell
                        masked_cell = mask_text(cell)
                        masked_row.append(masked_cell)
                    else:
                        masked_row.append(cell)

                    bytes_processed += len(cell.encode("utf-8"))

                # Aggregate row detections
                if row_detections:
                    all_detected.append(row_detections)

                    # Check policy for this row
                    decision, _, _ = policy.evaluate(destination, row_detections)
                    if decision == Decision.BLOCKED:
                        blocked_early = True
                        if stop_on_block:
                            break

                # Write row incrementally (constant memory usage)
                if output_writer:
                    output_writer.writerow(masked_row)

                rows_processed += 1

                if on_progress:
                    on_progress(rows_processed, bytes_processed)
    finally:
        if output_file:
            output_file.close()

    # Merge all detections
    merged_detected = _merge_detected_items(all_detected)

    # Final decision
    final_decision, final_summary, suggested_fix = policy.evaluate(
        destination, merged_detected
    )

    # Handle output path based on final decision
    if output_path:
        if final_decision == Decision.BLOCKED:
            # Remove output file if content is blocked
            try:
                output_path.unlink()
            except OSError:
                pass
        else:
            actual_output_path = str(output_path)

    return BatchProcessingResult(
        decision=final_decision,
        summary=final_summary,
        detected=merged_detected,
        suggested_fix=suggested_fix,
        bytes_processed=bytes_processed,
        chunks_processed=rows_processed,  # Using chunks for rows
        blocked_early=blocked_early,
        input_path=str(input_path),
        output_path=actual_output_path,
    )


class CSVStreamProcessor:
    """CSV-specific streaming processor.

    Optimized for processing large CSV files row by row with
    proper CSV parsing and selective column masking.

    Example:
        processor = CSVStreamProcessor()
        result = processor.process(
            "large_export.csv",
            "masked_export.csv",
            destination="VENDOR",
            columns_to_mask=[1, 2, 5],  # Only mask email, phone, ssn columns
        )
    """

    def __init__(
        self,
        policy_config: Optional[dict] = None,
        include_samples: bool = True,
    ):
        """Initialize CSV processor.

        Args:
            policy_config: Optional custom policy configuration
            include_samples: Whether to include masked samples
        """
        self.policy_config = policy_config
        self.include_samples = include_samples
        self.detector = PatternDetector(include_samples=include_samples)
        self.policy = PolicyEngine(policy_config)

    def process(
        self,
        input_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        destination: str = "AI_TOOL",
        has_header: bool = True,
        columns_to_mask: Optional[list[int]] = None,
        on_progress: Optional[Callable[[int, int], None]] = None,
        stop_on_block: bool = False,
    ) -> BatchProcessingResult:
        """Process a CSV file.

        Args:
            input_path: Path to input CSV file
            output_path: Optional path for masked output
            destination: Target destination
            has_header: Whether first row is header
            columns_to_mask: Column indices to mask (all if None)
            on_progress: Optional callback(rows, bytes)
            stop_on_block: Stop immediately if blocked

        Returns:
            BatchProcessingResult with results
        """
        return process_csv_file(
            input_path=input_path,
            output_path=output_path,
            destination=destination,
            has_header=has_header,
            columns_to_mask=columns_to_mask,
            policy_config=self.policy_config,
            include_samples=self.include_samples,
            on_progress=on_progress,
            stop_on_block=stop_on_block,
        )

    def detect_columns(
        self,
        file_path: Union[str, Path],
        sample_rows: int = 100,
    ) -> dict[int, list[str]]:
        """Detect which columns contain sensitive data.

        Samples the first N rows to identify which columns
        contain PII/PHI data.

        Args:
            file_path: Path to CSV file
            sample_rows: Number of rows to sample

        Returns:
            Dict mapping column index to list of detection types found
        """
        file_path = Path(file_path)
        column_detections: dict[int, set[str]] = {}

        with open(file_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)

            # Skip header
            next(reader, None)

            for row_idx, row in enumerate(reader):
                if row_idx >= sample_rows:
                    break

                for col_idx, cell in enumerate(row):
                    if cell:
                        detected = self.detector.detect(cell)
                        for item in detected:
                            if col_idx not in column_detections:
                                column_detections[col_idx] = set()
                            column_detections[col_idx].add(item.type)

        return {k: list(v) for k, v in column_detections.items()}

    def get_header(self, file_path: Union[str, Path]) -> list[str]:
        """Get header row from CSV file.

        Args:
            file_path: Path to CSV file

        Returns:
            List of column names
        """
        file_path = Path(file_path)
        with open(file_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader, [])
        return header
