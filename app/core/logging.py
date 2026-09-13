import logging
import sys


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure structured console logging without leaking sensitive information."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Clean existing handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(numeric_level)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    return logging.getLogger("hisabkitab.ai")


logger = setup_logging()
