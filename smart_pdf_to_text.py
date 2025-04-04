#!/usr/bin/env python3

import sys
import argparse
from pdf2markdown import convert_pdf_to_markdown

def pdf_to_markdown(pdf_path: str, output_path: str) -> bool:
    try:
        markdown = convert_pdf_to_markdown(pdf_path)
        with open(output_path, 'w', encoding='utf-8') as out_file:
            out_file.write(markdown)
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
