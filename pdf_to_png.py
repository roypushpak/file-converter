#!/usr/bin/env python3
import os
import argparse
from pathlib import Path
from pdf2image import convert_from_path

def convert_pdf_to_png(pdf_path, output_dir=None, dpi=200, fmt='png'):
    """
    Convert a PDF file to PNG images.
    
    Args:
        pdf_path (str): Path to the PDF file
        output_dir (str, optional): Directory to save the output images. Defaults to same as PDF.
        dpi (int, optional): DPI for the output image. Defaults to 200.
        fmt (str, optional): Output image format. Defaults to 'png'.
    
    Returns:
        list: List of paths to the generated image files
    """
    # Convert to Path object if it's a string
    pdf_path = Path(pdf_path)
    
    # Set output directory
    if output_dir is None:
        output_dir = pdf_path.parent
    else:
        output_dir = Path(output_dir)
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get the base filename without extension
    base_name = pdf_path.stem
    
    try:
        # Convert PDF to images
        images = convert_from_path(pdf_path, dpi=dpi)
        
        saved_files = []
        # Save each page as a separate image
        for i, image in enumerate(images, start=1):
            output_path = output_dir / f"{base_name}_page_{i:03d}.{fmt}"
            image.save(output_path, fmt.upper())
            saved_files.append(str(output_path))
            print(f"Saved: {output_path}")
            
        print(f"\nSuccessfully converted {len(images)} pages.")
        return saved_files
        
    except Exception as e:
        print(f"Error converting {pdf_path}: {str(e)}")
        return []

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Convert PDF files to PNG images.')
    parser.add_argument('pdf_path', help='Path to the PDF file')
    parser.add_argument('-o', '--output', help='Output directory (default: same as input file)')
    parser.add_argument('--dpi', type=int, default=200, help='DPI for the output image (default: 200)')
    parser.add_argument('--format', default='png', choices=['png', 'jpeg', 'jpg', 'tiff'], 
                        help='Output image format (default: png)')
    
    args = parser.parse_args()
    
    # Convert the PDF
    convert_pdf_to_png(
        pdf_path=args.pdf_path,
        output_dir=args.output,
        dpi=args.dpi,
        fmt=args.format.lower()
    )

if __name__ == "__main__":
    main()
