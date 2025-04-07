"""Logging configuration for PDF to Markdown converter."""

import logging
from typing import Optional


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure logging for the application.
    
    Args:
        verbose: If True, sets log level to DEBUG, otherwise INFO.
        
    Returns:
        Configured logger instance.
    """
    # Configure basic logging format
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format='%(message)s', 
        level=log_level
    )
    
    logger = logging.getLogger('pdf_converter')
    
    # Suppress library warnings
    for lib in ['fitz', 'PIL', 'pdfminer']:
        logging.getLogger(lib).setLevel(logging.ERROR)
    
    return logger


# Singleton logger instance
logger = setup_logging() 