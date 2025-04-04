#!/usr/bin/env python3

import sys
import argparse
import re
from io import StringIO
import pdfminer.layout as layout
import pdfminer.high_level as high_level
import pdfminer.pdfinterp as pdfinterp
import pdfminer.pdfpage as pdfpage
import pdfminer.converter as converter

def should_skip_text(text: str, text_element, page_height, margin_size=50):
    """Check if text element should be skipped"""
    # Skip if in header/footer area (y0 is bottom, y1 is top)
    y_bottom = text_element.y0
    y_top = text_element.y1
    x_left = text_element.x0
    x_right = text_element.x1
    
    text = text.strip()
    if not text:
        return True
    
    # Skip if text is in header/footer area
    if y_bottom < margin_size or y_top > page_height - margin_size:
        return True
            
    # Skip if text appears to be a header based on position and length
    if y_top > page_height - margin_size * 2:
        if len(text) < 50 or text.isupper():  # Short text or ALL CAPS in header area
            return True
            
    # Skip if text appears to be a footer
    if y_bottom < margin_size * 2:
        if len(text) < 50:  # Short text in footer area
            return True
    
    return False

def pdf_to_markdown(pdf_path: str, output_path: str) -> bool:
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
                        if text and not should_skip_text(text, element, page_height):
                            page_text.append(text)
                
                # Join text elements and add to output
                if page_text:
                    output_text.append('\n'.join(page_text))
        
        # Format and write the final text
        formatted_text = '\n\n'.join(output_text)
        # Basic formatting: Add markdown headers and preserve paragraphs
        formatted_text = formatted_text.replace('\f', '\n\n')  # Form feeds to double newlines
        # Clean up multiple newlines
        formatted_text = re.sub(r'\n{3,}', '\n\n', formatted_text)
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
    
    success = pdf_to_markdown(args.pdf_path, args.output_path)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
