"""
VibeDNA Logger

Structured logging utilities for VibeDNA operations.

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

import logging
import sys
from typing import Optional
from datetime import datetime


class VibeDNAFormatter(logging.Formatter):
    """Custom formatter for VibeDNA logs."""

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",      # Reset
    }

    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors and sys.stdout.isatty()

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname

        if self.use_colors:
            color = self.COLORS.get(level, self.COLORS["RESET"])
            reset = self.COLORS["RESET"]
            level_str = f"{color}{level:8}{reset}"
        else:
            level_str = f"{level:8}"

        message = record.getMessage()

        # Include extra context if provided
        extra_parts = []
        if hasattr(record, "operation"):
            extra_parts.append(f"op={record.operation}")
        if hasattr(record, "sequence_length"):
            extra_parts.append(f"seq_len={record.sequence_length}")
        if hasattr(record, "duration_ms"):
            extra_parts.append(f"duration={record.duration_ms}ms")

        extra_str = f" [{', '.join(extra_parts)}]" if extra_parts else ""

        return f"{timestamp} | {level_str} | {record.name} | {message}{extra_str}"


class VibeDNALogger(logging.Logger):
    """Extended logger with VibeDNA-specific methods."""

    def operation_start(self, operation: str, **kwargs) -> None:
        """Log the start of an operation."""
        extra = {"operation": operation, **kwargs}
        self.info(f"Starting {operation}", extra=extra)

    def operation_end(self, operation: str, duration_ms: float, **kwargs) -> None:
        """Log the end of an operation."""
        extra = {"operation": operation, "duration_ms": round(duration_ms, 2), **kwargs}
        self.info(f"Completed {operation}", extra=extra)

    def encoding_event(
        self,
        input_size: int,
        output_length: int,
        scheme: str,
        **kwargs
    ) -> None:
        """Log an encoding event."""
        ratio = output_length / (input_size * 4) if input_size > 0 else 0
        extra = {"operation": "encode", "sequence_length": output_length, **kwargs}
        self.info(
            f"Encoded {input_size} bytes → {output_length} nt (scheme={scheme}, ratio={ratio:.2f})",
            extra=extra
        )

    def decoding_event(
        self,
        input_length: int,
        output_size: int,
        errors_corrected: int = 0,
        **kwargs
    ) -> None:
        """Log a decoding event."""
        extra = {"operation": "decode", "sequence_length": input_length, **kwargs}
        msg = f"Decoded {input_length} nt → {output_size} bytes"
        if errors_corrected > 0:
            msg += f" (corrected {errors_corrected} errors)"
        self.info(msg, extra=extra)

    def error_correction_event(
        self,
        errors_detected: int,
        errors_corrected: int,
        **kwargs
    ) -> None:
        """Log an error correction event."""
        extra = {"operation": "error_correction", **kwargs}
        if errors_detected == 0:
            self.debug("No errors detected", extra=extra)
        elif errors_corrected == errors_detected:
            self.info(f"Corrected {errors_corrected} errors", extra=extra)
        else:
            self.warning(
                f"Detected {errors_detected} errors, corrected {errors_corrected}",
                extra=extra
            )


# Register custom logger class
logging.setLoggerClass(VibeDNALogger)

# Module-level logger cache
_loggers: dict = {}


def get_logger(name: str = "vibedna", level: Optional[int] = None) -> VibeDNALogger:
    """
    Get or create a VibeDNA logger.

    Args:
        name: Logger name (typically module name)
        level: Optional logging level override

    Returns:
        Configured VibeDNALogger instance
    """
    if name in _loggers:
        logger = _loggers[name]
        if level is not None:
            logger.setLevel(level)
        return logger

    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(VibeDNAFormatter())
        logger.addHandler(handler)

    if level is not None:
        logger.setLevel(level)
    else:
        logger.setLevel(logging.INFO)

    _loggers[name] = logger
    return logger  # type: ignore


def set_log_level(level: int) -> None:
    """Set log level for all VibeDNA loggers."""
    for logger in _loggers.values():
        logger.setLevel(level)


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
