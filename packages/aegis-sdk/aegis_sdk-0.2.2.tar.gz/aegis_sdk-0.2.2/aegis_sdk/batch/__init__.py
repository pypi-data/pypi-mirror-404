"""Batch processing module for large file handling.

This module provides streaming processors for handling large files
(200MB+) with constant memory usage (~30MB regardless of file size).
"""

from aegis_sdk.batch.processor import (
    StreamingProcessor,
    process_file,
    process_text_stream,
)
from aegis_sdk.batch.csv_processor import (
    CSVStreamProcessor,
    process_csv_file,
)

__all__ = [
    "StreamingProcessor",
    "process_file",
    "process_text_stream",
    "CSVStreamProcessor",
    "process_csv_file",
]
