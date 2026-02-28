"""
Logging configuration for the chat interface.
"""
import logging
import os
from datetime import datetime


def setup_logger(log_dir="logs", log_level=logging.INFO):
    """
    Setup application logging.
    
    Args:
        log_dir: Directory to store log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        Logger instance
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create log filename with timestamp
    log_filename = os.path.join(log_dir, f"chat_{datetime.now().strftime('%Y%m%d')}.log")
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger("ChatInterface")
    logger.info("Logger initialized")
    
    return logger


def get_logger(name):
    """Get a logger instance for a specific module."""
    return logging.getLogger(f"ChatInterface.{name}")
