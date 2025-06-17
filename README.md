# PDF to PNG Converter

A simple Python application to convert PDF files to PNG images with both command-line and graphical interfaces.

## Prerequisites

- Python 3.6+
- poppler-utils (required by pdf2image)

### Installing poppler-utils

#### macOS:
```bash
brew install poppler
```

#### Ubuntu/Debian:
```bash
sudo apt-get install poppler-utils
```

#### Windows:
Download and install poppler from: https://github.com/oschwartz10612/poppler-windows/releases/

## Installation

1. Clone this repository or download the files
2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Usage

### Command Line Interface

Basic usage:
```bash
python pdf_to_png.py input.pdf
```

With options:
```bash
python pdf_to_png.py input.pdf --output ./output_folder --dpi 300 --format jpeg
```

#### Arguments

- `pdf_path`: Path to the PDF file (required)
- `-o, --output`: Output directory (default: same as input file)
- `--dpi`: DPI for the output image (default: 200)
- `--format`: Output image format: png, jpeg, jpg, tiff (default: png)

### Graphical User Interface

To launch the GUI application:

```bash
python pdf_to_png_gui.py
```

The GUI provides a user-friendly interface to:
- Select PDF files using a file dialog
- Choose output directory
- Adjust DPI settings
- Preview the first page of the PDF
- View conversion progress

## Features

- **Command-line interface** for batch processing and automation
- **Graphical interface** for easy point-and-click operation
- **Preview** the first page of the PDF before conversion
- **Adjustable DPI** for high-quality output
- **Progress tracking** during conversion
- **Cross-platform** - works on Windows, macOS, and Linux

## Example

Convert `document.pdf` to PNG files with 300 DPI:
```bash
python pdf_to_png.py document.pdf --dpi 300
```

This will create PNG files named `document_page_001.png`, `document_page_002.png`, etc. in the same directory as the input file.
