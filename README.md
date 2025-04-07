# PDF to Markdown Converter

A powerful tool for converting PDF documents to Markdown format with intelligent section-based processing.

## Features

- Extracts text and images from PDF documents
- Preserves document structure using the PDF's Table of Contents (TOC)
- Organizes content into logical sections based on heading hierarchy
- Creates separate markdown files for each section
- Handles images properly with correct references
- Supports configurable chunking for better content organization
- Includes heading numbering with zero-padded subsection IDs

## Installation

Clone this repository:

```bash
git clone https://github.com/username/pdf-to-markdown.git
cd pdf-to-markdown
```

Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Convert a PDF to Markdown with default settings:

```bash
python smart_pdf_to_text.py input.pdf output.md
```

### Command-line Options

```
usage: smart_pdf_to_text.py [-h] [-c CONFIG] [-v] pdf_path output_path

Convert PDF to markdown

positional arguments:
  pdf_path              Path to input PDF file
  output_path           Path for output markdown file

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Path to custom config file
  -v, --verbose         Enable verbose logging
```

## Configuration

The converter behavior can be customized via the `config.yaml` file:

```yaml
margins:
  header_margin: 100    # Skip text in the top header area (px)
  footer_margin: 100    # Skip text in the bottom footer area (px)

formatting:
  max_newlines: 2       # Maximum consecutive newlines to preserve

images:
  output_dir: 'images'  # Directory for extracted images
  formats: ['jpg', 'png']  # Supported image formats
  min_size: 100         # Minimum image size to extract (px)

chunking:
  max_chars: 8000       # Maximum chunk size (~2000 words)
  overlap_chars: 500    # Overlap between chunks
  keep_full_file: true  # Keep full markdown in addition to chunks
  toc_level: 6          # Maximum section level to process (1-6)
```

## Output Structure

The converter creates the following output structure:

```
output/
├── images/                       # Extracted images
│   ├── image_p1_1.png
│   └── ...
├── 1_overview/                   # Section directories
│   ├── 1_0_overview_01.md
│   └── 1_01_scope_01.md
├── 2_network architecture/       # Another section
│   ├── 2_0_network architecture_01.md
│   └── ...
├── structure.yaml                # TOC structure
└── output.md                     # Full markdown file (optional)
```

## Output File Naming

Output files follow this naming pattern:
- Section directories: `{section_number}_{section_title}/`
- Chunk files: `{section_id_padded}_{section_title}_{chunk_number}.md`

Where:
- `section_id_padded` uses underscores instead of dots and zero-pads subsection numbers (e.g., `1_02_03` for section 1.2.3)
- For top-level sections, adds `_0` (e.g., `1_0` for section 1)
- Chunk numbers use two digits (e.g., `_01.md`)

## Development

### Running Tests

Run the unit tests:

```bash
python run_tests.py
```

### Project Structure

```
pdf_converter/
├── __init__.py                 # Package initialization
├── cli.py                      # Command-line interface
├── converter.py                # Main converter class
├── extract/                    # Extraction utilities
│   ├── __init__.py
│   ├── images.py               # Image extraction
│   └── text.py                 # Text extraction
├── formatting/                 # Text formatting
│   ├── __init__.py
│   └── chunking.py             # Text chunking
├── output/                     # Output management
│   ├── __init__.py
│   └── writer.py               # File writing
├── toc/                        # TOC handling
│   ├── __init__.py
│   └── extractor.py            # TOC extraction
└── utils/                      # Utilities
    ├── __init__.py
    ├── config.py               # Configuration loading
    └── logging.py              # Logging setup
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 