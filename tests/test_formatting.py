"""Tests for text formatting and chunking."""

import unittest
from pdf_converter.formatting.chunking import TextFormatter


class TestTextFormatter(unittest.TestCase):
    """Test cases for TextFormatter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'formatting': {'max_newlines': 2},
            'chunking': {
                'max_chars': 100,
                'overlap_chars': 20
            }
        }
        self.formatter = TextFormatter(self.config)
    
    def test_format_text(self):
        """Test format_text method."""
        # Test form feed replacement
        text = "Line 1\fLine 2"
        expected = "Line 1\n\nLine 2"
        self.assertEqual(self.formatter.format_text(text), expected)
        
        # Test newline limiting
        text = "Line 1\n\n\n\nLine 2"
        expected = "Line 1\n\nLine 2"
        self.assertEqual(self.formatter.format_text(text), expected)
        
        # Test whitespace trimming
        text = "Line 1   \nLine 2  "
        expected = "Line 1\nLine 2"
        self.assertEqual(self.formatter.format_text(text), expected)
    
    def test_add_section_header(self):
        """Test add_section_header method."""
        text = "This is the content."
        section_id = "1.2.3"
        section_title = "Test Section"
        level = 2
        
        expected = "## 1.2.3 Test Section\n\nThis is the content."
        
        result = self.formatter.add_section_header(text, section_id, section_title, level)
        self.assertEqual(result, expected)
    
    def test_split_into_chunks_basic(self):
        """Test split_into_chunks method with simple text."""
        # Create text that should fit into 2 chunks
        text = "A" * 60 + "\n\n" + "B" * 60
        
        chunks = self.formatter.split_into_chunks(text)
        
        self.assertEqual(len(chunks), 2)
        self.assertTrue(chunks[0].startswith("A"))
        self.assertTrue(chunks[1].startswith("B"))
    
    def test_split_into_chunks_long_paragraph(self):
        """Test split_into_chunks with a paragraph that exceeds chunk size."""
        # Create a long paragraph
        long_para = "Word. " * 60  # Each "Word. " is 6 chars, 60*6 = 360 chars
        
        chunks = self.formatter.split_into_chunks(long_para)
        
        # Should be split into at least 3 chunks (360/100 = 3.6)
        self.assertGreaterEqual(len(chunks), 3)
    
    def test_overlap_added(self):
        """Test that overlap is added between chunks."""
        # Test with two paragraphs that are just under the chunk size limit
        para1 = "A" * 50
        para2 = "B" * 50
        text = para1 + "\n\n" + para2
        
        # First get chunks without overlap to verify we have 2 chunks
        self.config['chunking']['overlap_chars'] = 0
        formatter_no_overlap = TextFormatter(self.config)
        chunks_no_overlap = formatter_no_overlap.split_into_chunks(text)
        self.assertEqual(len(chunks_no_overlap), 2)
        
        # Now test with overlap
        self.config['chunking']['overlap_chars'] = 20
        formatter_with_overlap = TextFormatter(self.config)
        chunks = formatter_with_overlap._add_overlap_to_chunks(chunks_no_overlap)
        
        # Should have 2 chunks
        self.assertEqual(len(chunks), 2)
        
        # Second chunk should start with overlap from first chunk
        self.assertTrue("A" in chunks[1])
        self.assertTrue("[previous chunk overlap]" in chunks[1])


if __name__ == '__main__':
    unittest.main() 