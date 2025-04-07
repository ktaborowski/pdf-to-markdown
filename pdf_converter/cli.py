"""Command-line interface for PDF to Markdown converter."""

import sys
import argparse
from pathlib import Path

from pdf_converter.utils.logging import logger, setup_logging
from pdf_converter.utils.config import load_config
from pdf_converter.converter import PDFConverter


def parse_args():
    """Parse command-line arguments.
    
    Returns:
        Parsed arguments object.
    """
    parser = argparse.ArgumentParser(description='Convert PDF to markdown')
    parser.add_argument('pdf_path', help='Path to input PDF file')
    parser.add_argument('output_path', help='Path for output markdown file')
    parser.add_argument('-c', '--config', help='Path to custom config file')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    
    return parser.parse_args()


def main():
    """Main entry point for the converter CLI."""
    args = parse_args()
    
    # Configure logging with verbosity
    logger = setup_logging(args.verbose)
    
    # Check if file exists
    pdf_path = Path(args.pdf_path)
    if not pdf_path.is_file():
        logger.error(f"Error: File not found: {pdf_path}")
        sys.exit(1)
    
    # Load configuration
    if args.config:
        config = load_config(Path(args.config))
    else:
        config = load_config()
    
    # Create converter and run conversion
    converter = PDFConverter(config)
    success = converter.convert(args.pdf_path, args.output_path)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main() 