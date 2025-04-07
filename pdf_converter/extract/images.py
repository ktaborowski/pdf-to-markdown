"""Image extraction functions for PDF to Markdown converter."""

import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pdf_converter.utils.logging import logger


class ImageExtractor:
    """Extracts images from PDF documents."""
    
    def __init__(self, config: dict):
        """Initialize with configuration settings.
        
        Args:
            config: Configuration dictionary containing image settings.
        """
        self.config = config
        self.min_size = config['images']['min_size']
        self.formats = config['images']['formats']
    
    def extract_images(self, pdf_path: str, image_dir: Path) -> Dict[str, List[str]]:
        """Extract images from PDF using PyMuPDF.
        
        Args:
            pdf_path: Path to the PDF file.
            image_dir: Directory to save extracted images.
            
        Returns:
            Dictionary mapping page numbers to lists of image filenames.
        """
        image_locations = {}
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        logger.info(f"Extracting images from {total_pages} pages...")
        
        for page_num in range(total_pages):
            self._process_page(doc, page_num, image_dir, image_locations)
            
        return image_locations
    
    def _process_page(self, doc: fitz.Document, page_num: int,
                     image_dir: Path, image_locations: Dict[str, List[str]]) -> None:
        """Process a single page of the PDF to extract images.
        
        Args:
            doc: PyMuPDF document object.
            page_num: Page number to process (0-indexed).
            image_dir: Directory to save images.
            image_locations: Dictionary to update with image locations.
        """
        page = doc[page_num]
        image_list = page.get_images()
        
        if image_list:
            logger.info(f"Found {len(image_list)} images on page {page_num + 1}")
        
        for img_idx, img in enumerate(image_list):
            try:
                self._save_image(doc, img, page_num, img_idx, image_dir, image_locations)
            except Exception as e:
                logger.error(f"Failed to save image from page {page_num + 1}: {e}")
    
    def _save_image(self, doc: fitz.Document, img: Tuple, page_num: int, 
                   img_idx: int, image_dir: Path, image_locations: Dict[str, List[str]]) -> None:
        """Extract and save a single image.
        
        Args:
            doc: PyMuPDF document object.
            img: Image tuple from PyMuPDF.
            page_num: Page number (0-indexed).
            img_idx: Image index on the page.
            image_dir: Directory to save the image.
            image_locations: Dictionary to update with image location.
        """
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        
        image = Image.open(BytesIO(image_bytes))
        
        # Skip small images
        if min(image.size) < self.min_size:
            return
        
        # Save with original format if supported, otherwise convert to PNG
        ext = base_image["ext"]
        if ext not in self.formats:
            ext = 'png'
        
        filename = f"image_p{page_num+1}_{img_idx+1}.{ext}"
        image_path = image_dir / filename
        image.save(image_path)
        
        # Store location for later insertion
        key = f"page_{page_num}"
        if key not in image_locations:
            image_locations[key] = []
        
        # Just store the filename
        image_locations[key].append(filename) 