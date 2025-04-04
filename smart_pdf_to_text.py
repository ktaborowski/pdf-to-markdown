#!/usr/bin/env python3

import sys
import argparse
import re
import yaml
from pathlib import Path
from io import StringIO
import pdfminer.layout as layout
import pdfminer.high_level as high_level
import pdfminer.pdfinterp as pdfinterp
import pdfminer.pdfpage as pdfpage
import pdfminer.converter as converter

def load_config():
    """Load configuration from YAML file"""
    config_path = Path(__file__).parent / 'config.yaml'
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        sys.exit(1)

def should_skip_text(text: str, text_element, page_height, config):
    """Check if text element should be skipped based on margins"""
    # Get coordinates
    y_bottom = text_element.y0
    y_top = text_element.y1
    
    # Skip if text is in header/footer area
    if (y_bottom < config['margins']['footer_margin'] or 
        y_top > page_height - config['margins']['header_margin']):
        return True
    
    return False

def pdf_to_markdown(pdf_path: str, output_path: str, config: dict) -> bool:
    try:
        output_text = []
        resource_manager = pdfinterp.PDFResourceManager()
        
        with open(pdf_path, 'rb') as pdf_file:
            for page_layout in high_level.extract_pages(pdf_file, laparams=layout.LAParams()):
                page_height = page_layout.height
                page_text = []
                
                # Process each text element on the page
                for element in page_layout:
                    if isinstance(element, layout.LTTextContainer):
                        text = element.get_text().strip()
                        if text and not should_skip_text(text, element, page_height, config):
                            page_text.append(text)
                
                # Join text elements and add to output
                if page_text:
                    output_text.append('\n'.join(page_text))
        
        # Format and write the final text
        formatted_text = '\n\n'.join(output_text)
        # Basic formatting: Add markdown headers and preserve paragraphs
        formatted_text = formatted_text.replace('\f', '\n\n')  # Form feeds to double newlines
        # Clean up multiple newlines
        max_newlines = '\n' * config['formatting']['max_newlines']
        formatted_text = re.sub(r'\n{3,}', max_newlines, formatted_text)
        # Clean up trailing whitespace
        formatted_text = '\n'.join(line.rstrip() for line in formatted_text.splitlines())
        
        with open(output_path, 'w', encoding='utf-8') as out_file:
            out_file.write(formatted_text)
        return True
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description='Convert PDF to markdown')
    parser.add_argument('pdf_path', help='Path to input PDF file')
    parser.add_argument('output_path', help='Path for output markdown file')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    success = pdf_to_markdown(args.pdf_path, args.output_path, config)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
