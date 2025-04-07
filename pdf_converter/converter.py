"""Main converter module for PDF to Markdown conversion."""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from pdf_converter.utils.logging import logger
from pdf_converter.extract.images import ImageExtractor
from pdf_converter.extract.text import TextExtractor
from pdf_converter.toc.extractor import TOCExtractor
from pdf_converter.formatting.chunking import TextFormatter
from pdf_converter.output.writer import OutputManager


class PDFConverter:
    """Main converter class for PDF to Markdown conversion."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration settings.
        
        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.image_extractor = ImageExtractor(config)
        self.text_extractor = TextExtractor(config)
        self.toc_extractor = TOCExtractor(config)
        self.text_formatter = TextFormatter(config)
        self.output_manager = OutputManager(config)
    
    def convert(self, pdf_path: str, output_path: str) -> bool:
        """Convert PDF to markdown.
        
        Args:
            pdf_path: Path to input PDF file.
            output_path: Path for output markdown file.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Setup directories and extract images
            output_path_obj = Path(output_path)
            base_path = output_path_obj.parent / output_path_obj.stem
            base_path.mkdir(exist_ok=True)
            
            # Extract images
            image_dir = self.output_manager.setup_image_dir(output_path)
            image_locations = self.image_extractor.extract_images(pdf_path, image_dir)
            
            # Extract TOC
            toc_structure = self.toc_extractor.extract_toc(pdf_path)
            self.output_manager.save_toc_structure(toc_structure, base_path)
            
            # Process the document
            if toc_structure:
                self._process_with_toc(pdf_path, output_path_obj, base_path, toc_structure, image_locations)
            else:
                self._process_without_toc(pdf_path, output_path_obj, base_path, image_locations)
            
            logger.info("Conversion completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False
    
    def _process_with_toc(self, pdf_path: str, output_path: Path, 
                         base_path: Path, toc_structure: Dict[str, Dict[str, Any]],
                         image_locations: Dict[str, List[str]]) -> None:
        """Process PDF using the TOC structure.
        
        Args:
            pdf_path: Path to input PDF file.
            output_path: Path for output file.
            base_path: Base directory for output.
            toc_structure: TOC structure dictionary.
            image_locations: Dictionary of image locations by page.
        """
        # Extract pages from PDF
        pages = self.text_extractor.extract_pages(pdf_path)
        
        # Sort sections by page and level
        sorted_sections = sorted(toc_structure.items(), 
                               key=lambda x: (x[1]['page'], x[1]['level']))
        logger.info(f"\nProcessing {len(sorted_sections)} subsections...")
        
        # Container for full text
        formatted_text = []
        
        # Process each section
        for i, (section_id, section) in enumerate(sorted_sections):
            # Determine page range
            start_page, end_page = self.toc_extractor.determine_section_pages(
                section_id, section, sorted_sections, i
            )
            
            # Create section directory
            top_level_id = section['id'].split('.')[0]
            top_level_section_data = toc_structure.get(top_level_id)
            
            if top_level_section_data:
                top_level_title = top_level_section_data['title']
            else:
                top_level_title = "unknown_section"
                
            section_output_dir = self.output_manager.create_section_dir(
                base_path, top_level_id, top_level_title
            )
            
            # Extract text
            text = self.text_extractor.extract_section_text(pages, start_page, end_page)
            
            # Add images
            for page_num in range(start_page - 1, end_page):
                key = f"page_{page_num}"
                if key in image_locations:
                    for img_path in image_locations[key]:
                        # Reference images directory at the same level as the section directory
                        img_ref_path = f"../images/{img_path}"
                        text = f"\n![Figure]({img_ref_path})\n" + text
            
            # Format text
            text = self.text_formatter.format_text(text)
            
            # Add section header
            text = self.text_formatter.add_section_header(
                text, section['id'], section['title'], section['level']
            )
            
            # Add to full text
            formatted_text.append(text)
            
            # Split into chunks
            chunks = self.text_formatter.split_into_chunks(text)
            
            # Write chunks
            self.output_manager.write_chunk_files(
                chunks, section_output_dir, section['id'], section['title']
            )
        
        # Write full file if requested
        self.output_manager.write_full_file(output_path, formatted_text)
    
    def _process_without_toc(self, pdf_path: str, output_path: Path, 
                            base_path: Path, image_locations: Dict[str, List[str]]) -> None:
        """Process PDF without TOC structure.
        
        Args:
            pdf_path: Path to input PDF file.
            output_path: Path for output file.
            base_path: Base directory for output.
            image_locations: Dictionary of image locations by page.
        """
        # Extract pages from PDF
        pages = self.text_extractor.extract_pages(pdf_path)
        total_pages = len(pages)
        logger.info(f"Processing {total_pages} pages...")
        
        # Process pages
        output_text = []
        
        for current_page, page_layout in enumerate(pages):
            page_height = page_layout.height
            page_text = []
            
            # Insert any images for this page
            page_key = f"page_{current_page}"
            if page_key in image_locations:
                for img_path in image_locations[page_key]:
                    # Reference the images directory
                    img_ref_path = f"images/{img_path}"
                    page_text.append(f"\n![Figure]({img_ref_path})\n")
            
            # Process text elements
            for element in page_layout:
                if isinstance(element, layout.LTTextContainer):
                    text = element.get_text().strip()
                    if text and not self.text_extractor.should_skip_text(text, element, page_height):
                        page_text.append(text)
            
            if page_text:
                output_text.append('\n'.join(page_text))
        
        # Join all text
        combined_text = '\n\n'.join(output_text)
        
        # Format text
        formatted_text = self.text_formatter.format_text(combined_text)
        
        # Split into chunks
        chunks = self.text_formatter.split_into_chunks(formatted_text)
        
        # Write chunks
        logger.info(f"\nWriting {len(chunks)} chunks...")
        for i, chunk in enumerate(chunks, 1):
            chunk_path = base_path / f"chunk_{i:03d}.md"
            with open(chunk_path, 'w', encoding='utf-8') as f:
                f.write(chunk)
            logger.info(f"Written chunk {i}/{len(chunks)}: {chunk_path}")
        
        # Write full file if requested
        self.output_manager.write_full_file(output_path, formatted_text) 