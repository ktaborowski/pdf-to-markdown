#!/usr/bin/env python3

import sys
import argparse
import re
import yaml
import logging
from pathlib import Path
from io import StringIO, BytesIO
import pdfminer.layout as layout
import pdfminer.high_level as high_level
import pdfminer.pdfinterp as pdfinterp
import pdfminer.pdfpage as pdfpage
import pdfminer.converter as converter
from PIL import Image
import fitz  # PyMuPDF

# Configure logging
logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger('pdf_converter')

# Suppress library warnings
logging.getLogger('fitz').setLevel(logging.ERROR)
logging.getLogger('PIL').setLevel(logging.ERROR)
logging.getLogger('pdfminer').setLevel(logging.ERROR)

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
    total_pages = len(doc)
    
    logger.info(f"Extracting images from {total_pages} pages...")
    for page_num in range(total_pages):
        page = doc[page_num]
        image_list = page.get_images()
        
        if image_list:
            logger.info(f"Found {len(image_list)} images on page {page_num + 1}")
        
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
                logger.error(f"Failed to save image from page {page_num + 1}: {e}")
    
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

def split_into_chunks(text: str, config: dict) -> list:
    """Split text into chunks based on configuration"""
    chunk_size = config['chunking']['max_chars']
    overlap = config['chunking']['overlap_chars']
    
    # Split text into paragraphs first
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = []
    current_size = 0
    
    for para in paragraphs:
        para_size = len(para)
        
        # If paragraph itself exceeds chunk size, split it
        if para_size > chunk_size:
            # Add current chunk if not empty
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
            
            # Split long paragraph while trying to maintain sentence boundaries
            sentences = re.split(r'(?<=[.!?])\s+', para)
            current_sentence = []
            current_sentence_size = 0
            
            for sentence in sentences:
                sentence_size = len(sentence)
                if current_sentence_size + sentence_size > chunk_size:
                    if current_sentence:
                        chunks.append(' '.join(current_sentence))
                    current_sentence = [sentence]
                    current_sentence_size = sentence_size
                else:
                    current_sentence.append(sentence)
                    current_sentence_size += sentence_size
            
            if current_sentence:
                chunks.append(' '.join(current_sentence))
            
        # If adding paragraph exceeds chunk size, start new chunk
        elif current_size + para_size > chunk_size:
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
            current_chunk = [para]
            current_size = para_size
        else:
            current_chunk.append(para)
            current_size += para_size
    
    # Add final chunk
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    # Add overlap if configured
    if overlap > 0:
        overlapped_chunks = []
        for i, chunk in enumerate(chunks):
            if i > 0:
                # Add overlap from previous chunk
                prev_chunk = chunks[i-1]
                overlap_text = prev_chunk[-overlap:]
                if overlap_text:
                    chunk = overlap_text + "\n\n... [previous chunk overlap] ...\n\n" + chunk
            overlapped_chunks.append(chunk)
        return overlapped_chunks
    
    return chunks

def get_section_pages(toc_structure: dict) -> list:
    """Get list of sections with their page ranges"""
    sections = []
    
    # Sort sections by their starting page
    sorted_sections = sorted(toc_structure.items(), key=lambda x: x[1]['page'])
    
    for i, (section_id, section) in enumerate(sorted_sections):
        # Get start page
        start_page = section['page']
        
        # End page is either start of next section or +10 pages if it's the last section
        if i < len(sorted_sections) - 1:
            end_page = sorted_sections[i + 1][1]['page']
        else:
            end_page = start_page + 10  # Assume last section is ~10 pages
        
        sections.append({
            'id': section_id,
            'title': section['title'],
            'start_page': start_page,
            'end_page': end_page,
            'subsections': section.get('subsections', {})
        })
    
    return sections

def extract_section_text(pages: list, start_page: int, end_page: int, config: dict) -> str:
    """Extract text from a range of pages"""
    section_text = []
    
    for page_num in range(start_page - 1, min(end_page - 1, len(pages))):
        page = pages[page_num]
        page_text = []
        
        # Get page height for margin calculations
        page_height = page.height
        
        # Process text elements
        for element in page:
            if isinstance(element, layout.LTTextContainer):
                text = element.get_text().strip()
                if text and not should_skip_text(text, element, page_height, config):
                    page_text.append(text)
        
        if page_text:
            section_text.append('\n'.join(page_text))
    
    return '\n\n'.join(section_text)

def pdf_to_markdown(pdf_path: str, output_path: str, config: dict, toc_structure: dict = None) -> bool:
    try:
        # Setup image directory and extract images
        image_dir = setup_image_dir(output_path, config)
        image_locations = extract_images(pdf_path, image_dir, config)
        
        # Create output directory
        output_path = Path(output_path)
        base_path = output_path.parent / output_path.stem
        base_path.mkdir(exist_ok=True)
        
        # Variable to store full text if needed
        formatted_text = []
        
        # Extract text using sections if TOC is available
        if toc_structure:
            sections = get_section_pages(toc_structure)
            logger.info(f"\nProcessing {len(sections)} sections...")
            
            with open(pdf_path, 'rb') as pdf_file:
                pages = list(high_level.extract_pages(pdf_file))
                
                for section in sections:
                    section_id = section['id']
                    section_title = section['title']
                    # Create directory using section title
                    section_dir = base_path / f"section_{section_title.lower().replace(' ', '_').replace('-', '_')}"
                    section_dir.mkdir(exist_ok=True)
                    
                    # Extract text for this section
                    text = extract_section_text(pages, section['start_page'], section['end_page'], config)
                    
                    # Add any images from the section's pages
                    for page_num in range(section['start_page'] - 1, section['end_page']):
                        key = f"page_{page_num}"
                        if key in image_locations:
                            for img_path in image_locations[key]:
                                text = f"\n![Figure]({img_path})\n" + text
                    
                    # Format the text
                    text = text.replace('\f', '\n\n')
                    max_newlines = '\n' * config['formatting']['max_newlines']
                    text = re.sub(r'\n{3,}', max_newlines, text)
                    text = '\n'.join(line.rstrip() for line in text.splitlines())
                    
                    # Add section header with title from TOC
                    text = f"Section: {section_title}\n\n{text}"
                    
                    # Add to full text
                    formatted_text.append(text)
                    
                    # Split into chunks if too large
                    chunks = split_into_chunks(text, config)
                    
                    # Write chunks
                    for i, chunk in enumerate(chunks, 1):
                        chunk_path = section_dir / f"chunk_{i:03d}.md"
                        with open(chunk_path, 'w', encoding='utf-8') as f:
                            f.write(chunk)
                        logger.info(f"Written: {chunk_path}")
                    
                    # Process subsections recursively
                    if section['subsections']:
                        # TODO: Add recursive subsection processing if needed
                        pass
        
        else:
            # Original processing without TOC
            with open(pdf_path, 'rb') as pdf_file:
                pages = list(high_level.extract_pages(pdf_file))
                total_pages = len(pages)
                logger.info(f"Processing {total_pages} pages...")
                
                output_text = []
                for current_page, page_layout in enumerate(pages):
                    page_height = page_layout.height
                    page_text = []
                    
                    # Insert any images for this page
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
                
                # Format the text
                formatted_text = '\n\n'.join(output_text)
                formatted_text = formatted_text.replace('\f', '\n\n')
                max_newlines = '\n' * config['formatting']['max_newlines']
                formatted_text = re.sub(r'\n{3,}', max_newlines, formatted_text)
                formatted_text = '\n'.join(line.rstrip() for line in formatted_text.splitlines())
                
                # Split into chunks
                chunks = split_into_chunks(formatted_text, config)
                
                # Write chunks
                logger.info(f"\nWriting {len(chunks)} chunks...")
                for i, chunk in enumerate(chunks, 1):
                    chunk_path = base_path / f"chunk_{i:03d}.md"
                    with open(chunk_path, 'w', encoding='utf-8') as f:
                        f.write(chunk)
                    logger.info(f"Written chunk {i}/{len(chunks)}: {chunk_path}")
        
        # Write full file if requested
        if config['chunking']['keep_full_file']:
            # Join sections with newlines if formatted_text is a list
            if isinstance(formatted_text, list):
                formatted_text = '\n\n'.join(formatted_text)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(formatted_text)
            logger.info(f"Written full file: {output_path}")
        
        logger.info("Conversion completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return False

def extract_pdf_toc(pdf_path: str) -> dict:
    """Extract built-in TOC/bookmarks from PDF"""
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()
    
    # Convert to dictionary structure
    toc_structure = {}
    current_sections = [None] * 6  # Track up to 6 levels
    
    for level, title, page in toc:
        # Create section entry
        section_entry = {
            'title': title,
            'page': page,
            'subsections': {},
        }
        
        # Update current section at this level
        current_sections[level-1] = section_entry
        
        # Reset deeper levels
        for i in range(level, len(current_sections)):
            current_sections[i] = None
        
        # Add to structure
        if level == 1:
            # Use title as key for top level since we don't have section numbers
            key = title.split()[0] if title else str(len(toc_structure) + 1)
            toc_structure[key] = section_entry
        else:
            parent = current_sections[level - 2]
            if parent:
                key = title.split()[0] if title else str(len(parent['subsections']) + 1)
                parent['subsections'][key] = section_entry
    
    # Save TOC structure
    with open('toc_structure.yaml', 'w') as f:
        yaml.dump(toc_structure, f, sort_keys=False)
    
    logger.info(f"Found {len(toc_structure)} top-level sections")
    logger.info("TOC structure saved to toc_structure.yaml")
    
    return toc_structure

def main():
    parser = argparse.ArgumentParser(description='Convert PDF to markdown')
    parser.add_argument('pdf_path', help='Path to input PDF file')
    parser.add_argument('output_path', help='Path for output markdown file')
    parser.add_argument('--extract-toc', action='store_true', help='Extract built-in TOC/bookmarks')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Extract TOC if requested
    toc_structure = None
    if args.extract_toc:
        toc_structure = extract_pdf_toc(args.pdf_path)
    
    success = pdf_to_markdown(args.pdf_path, args.output_path, config, toc_structure)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
