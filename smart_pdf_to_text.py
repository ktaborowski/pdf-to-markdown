#!/usr/bin/env python3

import sys
import argparse
from io import StringIO
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams

def pdf_to_markdown(pdf_path: str, output_path: str) -> bool:
    try:
        output = StringIO()
        with open(pdf_path, 'rb') as pdf_file:
            extract_text_to_fp(pdf_file, output, laparams=LAParams())
            
        markdown_text = output.getvalue()
        
        # Basic formatting: Add markdown headers and preserve paragraphs
        formatted_text = markdown_text.replace('\f', '\n\n')  # Form feeds to double newlines
        
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
