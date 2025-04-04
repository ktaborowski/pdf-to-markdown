#!/usr/bin/env python3

import sys
import argparse
import re
import yaml
from pathlib import Path
from io import StringIO, BytesIO
import pdfminer.layout as layout
import pdfminer.high_level as high_level
import pdfminer.pdfinterp as pdfinterp
import pdfminer.pdfpage as pdfpage
import pdfminer.converter as converter
from PIL import Image
import fitz  # PyMuPDF

def load_config():
    """Load configuration from YAML file"""
    config_path = Path(__file__).parent / 'config.yaml'
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        sys.exit(1)

def setup_image_dir(base_path: str, config: dict) -> Path:
    """Create and return path to image directory"""
    output_dir = Path(base_path).parent / config['images']['output_dir']
    output_dir.mkdir(exist_ok=True)
    return output_dir

def extract_images(pdf_path: str, image_dir: Path, config: dict) -> dict:
    """Extract images from PDF using PyMuPDF and return a mapping of image locations"""
    image_locations = {}
    doc = fitz.open(pdf_path)
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images()
        
        for img_idx, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            
            try:
                image = Image.open(BytesIO(image_bytes))
                if min(image.size) < config['images']['min_size']:
                    continue
                    
                # Save with original format if supported, otherwise convert to PNG
                ext = base_image["ext"]
                if ext not in config['images']['formats']:
                    ext = 'png'
                    
                filename = f"image_p{page_num+1}_{img_idx+1}.{ext}"
                image_path = image_dir / filename
                image.save(image_path)
                
                # Store location for later insertion
                key = f"page_{page_num}"
                if key not in image_locations:
                    image_locations[key] = []
                image_locations[key].append(str(Path(config['images']['output_dir']) / filename))
                
            except Exception as e:
                print(f"Failed to save image: {e}", file=sys.stderr)
    
    return image_locations

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
        image_dir = setup_image_dir(output_path, config)
        
        # Extract images first
        image_locations = extract_images(pdf_path, image_dir, config)
        
        # Process text and insert images
        with open(pdf_path, 'rb') as pdf_file:
            current_page = -1
            for page_layout in high_level.extract_pages(pdf_file, laparams=layout.LAParams()):
                current_page += 1
                page_height = page_layout.height
                page_text = []
                
                # Insert any images for this page at the start
                page_key = f"page_{current_page}"
                if page_key in image_locations:
                    for img_path in image_locations[page_key]:
                        page_text.append(f"\n![Figure]({img_path})\n")
                
                # Process text elements
                for element in page_layout:
                    if isinstance(element, layout.LTTextContainer):
                        text = element.get_text().strip()
                        if text and not should_skip_text(text, element, page_height, config):
                            page_text.append(text)
                
                if page_text:
                    output_text.append('\n'.join(page_text))
        
        # Format and write the final text
        formatted_text = '\n\n'.join(output_text)
        formatted_text = formatted_text.replace('\f', '\n\n')  # Form feeds to double newlines
        max_newlines = '\n' * config['formatting']['max_newlines']
        formatted_text = re.sub(r'\n{3,}', max_newlines, formatted_text)
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
