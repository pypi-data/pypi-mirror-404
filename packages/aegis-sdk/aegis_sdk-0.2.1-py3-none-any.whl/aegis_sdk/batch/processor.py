"""Streaming file processor for large files.

This module provides constant-memory processing of large files (200MB+)
by reading and processing in configurable chunks.

Memory profile: ~2x chunk_size (read buffer + write buffer)
For 10MB chunks: ~20-30MB RAM regardless of file size.
"""

import os
from pathlib import Path
from typing import Callable, Iterator, Optional, TextIO, Union

from aegis_sdk.types import (
    Decision,
    DetectedItem,
    ProcessingResult,
    BatchProcessingResult,
)
from aegis_sdk.core.detector import PatternDetector, aggregate_findings, detect_patterns
from aegis_sdk.core.masker import mask_text
from aegis_sdk.core.policy import PolicyEngine, evaluate_decision


# Default chunk size: 10MB
DEFAULT_CHUNK_SIZE_MB = 10
DEFAULT_CHUNK_SIZE = DEFAULT_CHUNK_SIZE_MB * 1024 * 1024


def _read_chunks(
    file_handle: TextIO,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = 1000,
) -> Iterator[tuple[str, int]]:
    """Read file in chunks with overlap to handle pattern boundaries.

    The overlap ensures patterns spanning chunk boundaries are detected.
    Each chunk includes `overlap` characters from the previous chunk.

    Args:
        file_handle: Open file handle to read from
        chunk_size: Size of each chunk in bytes
        overlap: Number of characters to overlap between chunks

    Yields:
        Tuple of (chunk_text, bytes_read)
    """
    buffer = ""
    total_read = 0

    while True:
        # Read next chunk
        data = file_handle.read(chunk_size)
        if not data:
            # Yield remaining buffer
            if buffer:
                yield buffer, len(buffer.encode("utf-8"))
            break

        # Combine with leftover from previous chunk
        combined = buffer + data
        total_read += len(data.encode("utf-8"))

        # Keep overlap for next iteration
        if len(combined) > overlap:
            yield combined[:-overlap], len(combined[:-overlap].encode("utf-8"))
            buffer = combined[-overlap:]
        else:
            buffer = combined


def _merge_detected_items(items_list: list[list[DetectedItem]]) -> list[DetectedItem]:
    """Merge detected items from multiple chunks.

    Aggregates counts for same detection types across chunks.

    Args:
        items_list: List of detected item lists from each chunk

    Returns:
        Single merged list with aggregated counts
    """
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


def process_text_stream(
    text_iterator: Iterator[str],
    destination: str = "AI_TOOL",
    policy_config: Optional[dict] = None,
    include_samples: bool = True,
    on_chunk: Optional[Callable[[int, int], None]] = None,
) -> BatchProcessingResult:
    """Process text from an iterator with streaming.

    Args:
        text_iterator: Iterator yielding text chunks
        destination: Target destination for policy evaluation
        policy_config: Optional custom policy configuration
        include_samples: Whether to include masked samples
        on_chunk: Optional callback(chunks_processed, bytes_processed)

    Returns:
        BatchProcessingResult with aggregated results
    """
    detector = PatternDetector(include_samples=include_samples)
    policy = PolicyEngine(policy_config)

    all_detected: list[list[DetectedItem]] = []
    bytes_processed = 0
    chunks_processed = 0
    blocked = False
    block_reason: Optional[str] = None

    for chunk in text_iterator:
        # Detect in this chunk
        detected = detector.detect(chunk)
        all_detected.append(detected)

        # Check if this chunk would cause blocking
        decision, summary, _ = policy.evaluate(destination, detected)
        if decision == Decision.BLOCKED:
            blocked = True
            block_reason = summary

        bytes_processed += len(chunk.encode("utf-8"))
        chunks_processed += 1

        if on_chunk:
            on_chunk(chunks_processed, bytes_processed)

    # Merge all detections
    merged_detected = _merge_detected_items(all_detected)

    # Final decision based on all detected items
    final_decision, final_summary, suggested_fix = policy.evaluate(
        destination, merged_detected
    )

    return BatchProcessingResult(
        decision=final_decision,
        summary=final_summary,
        detected=merged_detected,
        suggested_fix=suggested_fix,
        bytes_processed=bytes_processed,
        chunks_processed=chunks_processed,
        blocked_early=blocked,
    )


def process_file(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    destination: str = "AI_TOOL",
    chunk_size_mb: int = DEFAULT_CHUNK_SIZE_MB,
    policy_config: Optional[dict] = None,
    include_samples: bool = True,
    on_progress: Optional[Callable[[int, int, int], None]] = None,
    stop_on_block: bool = False,
) -> BatchProcessingResult:
    """Process a large file with streaming and constant memory.

    This function reads the input file in chunks, detects sensitive data,
    and optionally writes masked output. Memory usage stays constant
    regardless of file size.

    Args:
        input_path: Path to input file
        output_path: Optional path for masked output file
        destination: Target destination for policy evaluation
        chunk_size_mb: Chunk size in megabytes (default 10)
        policy_config: Optional custom policy configuration
        include_samples: Whether to include masked samples
        on_progress: Optional callback(bytes_processed, total_bytes, chunks)
        stop_on_block: Stop processing immediately if blocked

    Returns:
        BatchProcessingResult with processing results

    Example:
        result = process_file(
            "large_data.txt",
            "masked_data.txt",
            destination="VENDOR",
            on_progress=lambda b, t, c: print(f"{b/t*100:.1f}% complete")
        )
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    total_bytes = input_path.stat().st_size
    chunk_size = int(chunk_size_mb * 1024 * 1024)
    overlap = min(1000, chunk_size // 10)  # 1KB or 10% of chunk

    detector = PatternDetector(include_samples=include_samples)
    policy = PolicyEngine(policy_config)

    all_detected: list[list[DetectedItem]] = []
    bytes_processed = 0
    chunks_processed = 0
    blocked_early = False
    output_file: Optional[TextIO] = None

    try:
        # Open output file if specified
        if output_path:
            output_path = Path(output_path)
            output_file = open(output_path, "w", encoding="utf-8")

        with open(input_path, "r", encoding="utf-8") as infile:
            buffer = ""

            while True:
                # Read chunk
                data = infile.read(chunk_size)
                if not data:
                    # Process remaining buffer
                    if buffer:
                        detected = detector.detect(buffer)
                        all_detected.append(detected)

                        decision, _, _ = policy.evaluate(destination, detected)
                        if decision == Decision.BLOCKED:
                            blocked_early = True
                            if stop_on_block:
                                break

                        if output_file and decision != Decision.BLOCKED:
                            masked = mask_text(buffer)
                            output_file.write(masked)

                        bytes_processed += len(buffer.encode("utf-8"))
                        chunks_processed += 1
                    break

                # Combine with buffer
                combined = buffer + data

                # Process main content (keep overlap for next iteration)
                if len(combined) > overlap:
                    to_process = combined[:-overlap]
                    buffer = combined[-overlap:]
                else:
                    to_process = combined
                    buffer = ""

                # Detect sensitive data
                detected = detector.detect(to_process)
                all_detected.append(detected)

                # Check decision
                decision, _, _ = policy.evaluate(destination, detected)
                if decision == Decision.BLOCKED:
                    blocked_early = True
                    if stop_on_block:
                        break

                # Write masked output
                if output_file and decision != Decision.BLOCKED:
                    masked = mask_text(to_process)
                    output_file.write(masked)

                bytes_processed += len(to_process.encode("utf-8"))
                chunks_processed += 1

                if on_progress:
                    on_progress(bytes_processed, total_bytes, chunks_processed)

    finally:
        if output_file:
            output_file.close()

    # Merge all detections
    merged_detected = _merge_detected_items(all_detected)

    # Final decision
    final_decision, final_summary, suggested_fix = policy.evaluate(
        destination, merged_detected
    )

    # If blocked and output was created, optionally remove it
    if final_decision == Decision.BLOCKED and output_path:
        output_path = Path(output_path)
        if output_path.exists():
            output_path.unlink()

    return BatchProcessingResult(
        decision=final_decision,
        summary=final_summary,
        detected=merged_detected,
        suggested_fix=suggested_fix,
        bytes_processed=bytes_processed,
        chunks_processed=chunks_processed,
        blocked_early=blocked_early,
        input_path=str(input_path),
        output_path=str(output_path) if output_path and final_decision != Decision.BLOCKED else None,
    )


class StreamingProcessor:
    """Streaming processor for large files with constant memory usage.

    This class provides an object-oriented interface for processing
    large files (200MB+) without loading them entirely into memory.

    Example:
        processor = StreamingProcessor(chunk_size_mb=10)
        result = processor.process_file(
            "large_export.csv",
            "masked_export.csv",
            destination="VENDOR",
            on_progress=lambda b, t, c: print(f"Processed {b/1e6:.1f}MB")
        )
    """

    def __init__(
        self,
        chunk_size_mb: int = DEFAULT_CHUNK_SIZE_MB,
        policy_config: Optional[dict] = None,
        include_samples: bool = True,
    ):
        """Initialize streaming processor.

        Args:
            chunk_size_mb: Chunk size in megabytes (default 10)
            policy_config: Optional custom policy configuration
            include_samples: Whether to include masked samples
        """
        self.chunk_size_mb = chunk_size_mb
        self.policy_config = policy_config
        self.include_samples = include_samples
        self.detector = PatternDetector(include_samples=include_samples)
        self.policy = PolicyEngine(policy_config)

    def process_file(
        self,
        input_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        destination: str = "AI_TOOL",
        on_progress: Optional[Callable[[int, int, int], None]] = None,
        stop_on_block: bool = False,
    ) -> BatchProcessingResult:
        """Process a file with streaming.

        Args:
            input_path: Path to input file
            output_path: Optional path for masked output
            destination: Target destination
            on_progress: Optional callback(bytes, total, chunks)
            stop_on_block: Stop immediately if blocked

        Returns:
            BatchProcessingResult with results
        """
        return process_file(
            input_path=input_path,
            output_path=output_path,
            destination=destination,
            chunk_size_mb=self.chunk_size_mb,
            policy_config=self.policy_config,
            include_samples=self.include_samples,
            on_progress=on_progress,
            stop_on_block=stop_on_block,
        )

    def process_stream(
        self,
        text_iterator: Iterator[str],
        destination: str = "AI_TOOL",
        on_chunk: Optional[Callable[[int, int], None]] = None,
    ) -> BatchProcessingResult:
        """Process text from a stream/iterator.

        Args:
            text_iterator: Iterator yielding text chunks
            destination: Target destination
            on_chunk: Optional callback(chunks, bytes)

        Returns:
            BatchProcessingResult with results
        """
        return process_text_stream(
            text_iterator=text_iterator,
            destination=destination,
            policy_config=self.policy_config,
            include_samples=self.include_samples,
            on_chunk=on_chunk,
        )

    def estimate_memory_usage(self, chunk_size_mb: Optional[int] = None) -> dict:
        """Estimate memory usage for processing.

        Args:
            chunk_size_mb: Optional override for chunk size

        Returns:
            Dict with memory estimates in MB
        """
        chunk = chunk_size_mb or self.chunk_size_mb
        return {
            "chunk_size_mb": chunk,
            "read_buffer_mb": chunk,
            "write_buffer_mb": chunk,
            "overhead_mb": 10,
            "total_estimated_mb": chunk * 2 + 10,
        }
