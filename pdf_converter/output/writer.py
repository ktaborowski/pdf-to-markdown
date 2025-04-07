"""Output file and directory management for PDF to Markdown converter."""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional

from pdf_converter.utils.logging import logger


class OutputManager:
    """Manages file output and directory structure for the converter."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration settings.
        
        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.keep_full_file = config['chunking']['keep_full_file']
    
    def setup_image_dir(self, base_path: str) -> Path:
        """Create and return path to image directory.
        
        Args:
            base_path: Base path for output.
            
        Returns:
            Path to the image directory.
        """
        # Create the base output directory if it doesn't exist
        output_base = Path(base_path).parent / Path(base_path).stem
        output_base.mkdir(exist_ok=True)
        
        # Create images directory inside the output directory
        output_dir = output_base / self.config['images']['output_dir']
        output_dir.mkdir(exist_ok=True)
        return output_dir
    
    def save_toc_structure(self, toc_structure: Dict[str, Dict], base_path: Path) -> None:
        """Save TOC structure to YAML file.
        
        Args:
            toc_structure: The TOC structure dictionary.
            base_path: Base path for output.
        """
        with open(base_path / 'structure.yaml', 'w') as f:
            yaml.dump(toc_structure, f, sort_keys=False)
        logger.info("TOC structure saved to structure.yaml")
    
    def create_section_dir(self, base_path: Path, section_id: str, 
                          top_level_title: str) -> Path:
        """Create a directory for a section.
        
        Args:
            base_path: Base path for output.
            section_id: Section ID.
            top_level_title: Title of the top-level section.
            
        Returns:
            Path to the created directory.
        """
        section_title_sanitized = top_level_title.lower().replace('/', '_').replace('\\', '_')
        section_dir = base_path / f"{section_id}_{section_title_sanitized}"
        section_dir.mkdir(exist_ok=True)
        return section_dir
    
    def format_section_id(self, section_id: str) -> str:
        """Format section ID with zero-padded subsections.
        
        Args:
            section_id: Original section ID (e.g., "1.2.3").
            
        Returns:
            Formatted section ID (e.g., "1_02_03" or "1_0" for top-level).
        """
        parts = section_id.split('.')
        padded_parts = []
        
        for i, part in enumerate(parts):
            # First level doesn't need padding
            if i == 0:
                padded_parts.append(part)
            else:
                # Pad subsection numbers with zeros (2 digits)
                padded_parts.append(f"{int(part):02d}")
                
        section_id_padded = '_'.join(padded_parts)
        
        # For top level sections, add _0
        if len(parts) == 1:
            section_id_padded = f"{section_id_padded}_0"
            
        return section_id_padded
    
    def write_chunk_files(self, chunks: List[str], section_output_dir: Path, 
                         section_id: str, section_title: str) -> None:
        """Write chunks to files with appropriate naming.
        
        Args:
            chunks: List of text chunks.
            section_output_dir: Directory to write files to.
            section_id: Section ID.
            section_title: Section title.
        """
        # Sanitize title for filename
        section_title_sanitized = section_title.lower().replace('/', '_').replace('\\', '_')
        
        # Format section ID with zero-padded subsections
        section_id_padded = self.format_section_id(section_id)

        # Write each chunk to a file
        for j, chunk in enumerate(chunks, 1):
            chunk_filename = f"{section_id_padded}_{section_title_sanitized}_{j:02d}.md"
            chunk_path = section_output_dir / chunk_filename
            
            with open(chunk_path, 'w', encoding='utf-8') as f:
                f.write(chunk)
                
            logger.info(f"Written: {chunk_path}")
    
    def write_full_file(self, output_path: Path, formatted_text: Any) -> None:
        """Write the full text to a single file.
        
        Args:
            output_path: Path to write the file.
            formatted_text: Text content (string or list).
        """
        if not self.keep_full_file:
            return
            
        # Join sections with newlines if formatted_text is a list
        if isinstance(formatted_text, list):
            formatted_text = '\n\n'.join(formatted_text)
            
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted_text)
            
        logger.info(f"Written full file: {output_path}") 