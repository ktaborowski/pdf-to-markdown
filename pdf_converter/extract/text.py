"""Text extraction functions for PDF to Markdown converter."""

import pdfminer.layout as layout
import pdfminer.high_level as high_level
from pathlib import Path
from typing import List, Dict, Any

from pdf_converter.utils.logging import logger


class TextExtractor:
    """Extracts text from PDF documents respecting margins and layout."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration settings.
        
        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.header_margin = config['margins']['header_margin']
        self.footer_margin = config['margins']['footer_margin']
    
    def extract_pages(self, pdf_path: str) -> List[layout.LTPage]:
        """Extract all pages from the PDF.
        
        Args:
            pdf_path: Path to the PDF file.
            
        Returns:
            List of PDF pages for further processing.
        """
        with open(pdf_path, 'rb') as pdf_file:
            return list(high_level.extract_pages(pdf_file))
    
    def should_skip_text(self, text: str, text_element: layout.LTTextContainer, 
                         page_height: float) -> bool:
        """Check if text element should be skipped based on margins.
        
        Args:
            text: The text content.
            text_element: The text container element.
            page_height: Height of the page.
            
        Returns:
            True if the text should be skipped, False otherwise.
        """
        # Get coordinates
        y_bottom = text_element.y0
        y_top = text_element.y1
        
        # Skip if text is in header/footer area
        if (y_bottom < self.footer_margin or 
            y_top > page_height - self.header_margin):
            return True
        
        return False
    
    def extract_section_text(self, pages: List[layout.LTPage], 
                            start_page: int, end_page: int) -> str:
        """Extract text from a range of pages.
        
        Args:
            pages: List of all pages.
            start_page: Starting page number (1-indexed).
            end_page: Ending page number (1-indexed).
            
        Returns:
            Extracted text from the section.
        """
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
                    if text and not self.should_skip_text(text, element, page_height):
                        page_text.append(text)
            
            if page_text:
                section_text.append('\n'.join(page_text))
        
        return '\n\n'.join(section_text) 