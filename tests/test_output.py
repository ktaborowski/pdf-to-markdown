"""Tests for the output module."""

import unittest
import tempfile
import shutil
from pathlib import Path
from pdf_converter.output.writer import OutputManager


class TestOutputManager(unittest.TestCase):
    """Test cases for OutputManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_dir = Path(self.temp_dir)
        self.config = {
            'images': {'output_dir': 'images'},
            'chunking': {'keep_full_file': True},
        }
        self.output_manager = OutputManager(self.config)
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Clean up the temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_setup_image_dir(self):
        """Test setup_image_dir method."""
        # Create a test output path
        output_path = str(self.test_dir / "output.md")
        
        # Call the method
        image_dir = self.output_manager.setup_image_dir(output_path)
        
        # Check that the image directory was created
        expected_path = self.test_dir / "output" / "images"
        self.assertEqual(image_dir, expected_path)
        self.assertTrue(expected_path.exists())
        self.assertTrue(expected_path.is_dir())
    
    def test_create_section_dir(self):
        """Test create_section_dir method."""
        # Call the method
        section_dir = self.output_manager.create_section_dir(
            self.test_dir, "1", "Test Section"
        )
        
        # Check that the section directory was created
        expected_path = self.test_dir / "1_test section"
        self.assertEqual(section_dir, expected_path)
        self.assertTrue(expected_path.exists())
        self.assertTrue(expected_path.is_dir())
    
    def test_format_section_id(self):
        """Test format_section_id method."""
        # Test top-level section
        self.assertEqual(self.output_manager.format_section_id("1"), "1_0")
        
        # Test section with one level
        self.assertEqual(self.output_manager.format_section_id("1.2"), "1_02")
        
        # Test section with multiple levels
        self.assertEqual(self.output_manager.format_section_id("1.2.3"), "1_02_03")
        
        # Test double-digit section numbers
        self.assertEqual(self.output_manager.format_section_id("10.11.12"), "10_11_12")
    
    def test_write_chunk_files(self):
        """Test write_chunk_files method."""
        # Create test data
        chunks = ["Chunk 1 content", "Chunk 2 content"]
        section_id = "1.2"
        section_title = "Test Section"
        
        # Call the method
        self.output_manager.write_chunk_files(
            chunks, self.test_dir, section_id, section_title
        )
        
        # Check that chunk files were created
        expected_path1 = self.test_dir / "1_02_test section_01.md"
        expected_path2 = self.test_dir / "1_02_test section_02.md"
        
        self.assertTrue(expected_path1.exists())
        self.assertTrue(expected_path2.exists())
        
        # Check content
        with open(expected_path1, 'r') as f:
            self.assertEqual(f.read(), "Chunk 1 content")
        
        with open(expected_path2, 'r') as f:
            self.assertEqual(f.read(), "Chunk 2 content")
    
    def test_write_full_file(self):
        """Test write_full_file method."""
        # Test with string content
        content = "Full file content"
        output_path = self.test_dir / "full_output.md"
        
        self.output_manager.write_full_file(output_path, content)
        
        self.assertTrue(output_path.exists())
        with open(output_path, 'r') as f:
            self.assertEqual(f.read(), content)
        
        # Test with list content
        content_list = ["Section 1", "Section 2", "Section 3"]
        output_path2 = self.test_dir / "full_output2.md"
        
        self.output_manager.write_full_file(output_path2, content_list)
        
        self.assertTrue(output_path2.exists())
        with open(output_path2, 'r') as f:
            self.assertEqual(f.read(), "Section 1\n\nSection 2\n\nSection 3")


if __name__ == '__main__':
    unittest.main() 