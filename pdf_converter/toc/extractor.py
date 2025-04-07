"""Table of Contents extraction for PDF to Markdown converter."""

import fitz  # PyMuPDF
from typing import Dict, List, Tuple, Any

from pdf_converter.utils.logging import logger


class TOCExtractor:
    """Extracts and processes Table of Contents from PDF documents."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration settings.
        
        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.max_level = config['chunking'].get('toc_level', 6)
    
    def extract_toc(self, pdf_path: str) -> Dict[str, Dict[str, Any]]:
        """Extract built-in TOC/bookmarks from PDF.
        
        Args:
            pdf_path: Path to the PDF file.
            
        Returns:
            Dictionary containing structured TOC with section IDs as keys.
        """
        doc = fitz.open(pdf_path)
        toc = doc.get_toc()
        
        # Convert to flattened dictionary structure
        toc_structure = {}
        current_path = []  # Track current path in TOC hierarchy
        section_counters = [0] * self.max_level  # Track section numbers at each level
        
        for level, title, page in toc:
            # Skip if level is beyond max_level
            if level > self.max_level:
                continue
                
            # Adjust current path based on level
            if level <= len(current_path):
                current_path = current_path[:level-1]
            current_path.append(title)
            
            # Update section counters
            section_counters[level-1] += 1
            # Reset deeper levels
            for i in range(level, self.max_level):
                section_counters[i] = 0
                
            # Create section ID (e.g. "1.2.3")
            section_id = '.'.join(str(num) for num in section_counters[:level] if num > 0)
            
            # Create section entry
            section_entry = {
                'title': title,
                'page': page,
                'level': level,
                'id': section_id,
                'full_path': current_path.copy()  # Store full path for reference
            }
            
            # Use section_id as key
            toc_structure[section_id] = section_entry

        logger.info(f"Found {len(toc_structure)} subsections")
        return toc_structure
    
    def determine_section_pages(self, 
                               section_id: str, 
                               section: Dict[str, Any], 
                               sorted_sections: List[Tuple[str, Dict[str, Any]]], 
                               current_index: int) -> Tuple[int, int]:
        """Determine accurate start and end pages for a section.
        
        Args:
            section_id: The section ID.
            section: The section data.
            sorted_sections: All sections sorted by page number.
            current_index: Index of the current section in sorted_sections.
            
        Returns:
            Tuple of (start_page, end_page)
        """
        start_page = section['page']
        level = section['level']
        current_full_path = section['full_path']
        
        # --- Determine accurate end_page --- 
        end_page = None
        first_child_page = None
        
        # Look for first child
        for j in range(current_index + 1, len(sorted_sections)):
            next_sec_id, next_sec_data = sorted_sections[j]
            if (next_sec_data['level'] == level + 1 and 
                next_sec_data['full_path'][:-1] == current_full_path):
                first_child_page = next_sec_data['page']
                break
        
        # Look for next sibling or cousin (same or higher level)
        next_sibling_or_cousin_page = None
        for j in range(current_index + 1, len(sorted_sections)):
            next_sec_id, next_sec_data = sorted_sections[j]
            if next_sec_data['level'] <= level:
                next_sibling_or_cousin_page = next_sec_data['page']
                break
        
        # Determine end page based on children and siblings
        if first_child_page is not None and (next_sibling_or_cousin_page is None or 
                                           first_child_page <= next_sibling_or_cousin_page):
            end_page = first_child_page
        elif next_sibling_or_cousin_page is not None:
            end_page = next_sibling_or_cousin_page
        else:
            end_page = start_page + 10  # Default to 10 pages if no better reference
        
        # Ensure end_page >= start_page
        if end_page < start_page:
            end_page = start_page
            
        return start_page, end_page 