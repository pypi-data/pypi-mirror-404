"""
Logging configuration for QuickSearch.
"""
import logging
import sys


def setup_logging(level=logging.INFO, log_file=None):
    """
    Configure logging for QuickSearch.
    
    Args:
        level: Logging level (default: INFO)
        log_file: Optional file path to write logs to
    """
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    # Reduce noise from external libraries
    logging.getLogger('motor').setLevel(logging.WARNING)
    logging.getLogger('pymongo').setLevel(logging.WARNING)


def get_logger(name):
    """Get a logger instance."""
    return logging.getLogger(f"quicksearch.{name}")
