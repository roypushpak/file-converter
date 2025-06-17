#!/usr/bin/env python3
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Optional
from pdf2image import convert_from_path
from PIL import Image, ImageTk
import threading

class PDFToPNGConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF to PNG Converter")
        self.root.geometry("600x400")
        self.root.minsize(500, 350)
        
        # Variables
        self.pdf_path = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.dpi = tk.IntVar(value=200)
        self.status = tk.StringVar(value="Ready")
        self.progress = tk.DoubleVar()
        self.conversion_in_progress = False
        
        self.setup_ui()
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # PDF File Selection
        file_frame = ttk.LabelFrame(main_frame, text="PDF File", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Entry(file_frame, textvariable=self.pdf_path, state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(file_frame, text="Browse...", command=self.browse_pdf).pack(side=tk.RIGHT)
        
        # Output Directory Selection
        output_frame = ttk.LabelFrame(main_frame, text="Output Directory", padding="10")
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Entry(output_frame, textvariable=self.output_dir, state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(output_frame, text="Browse...", command=self.browse_output_dir).pack(side=tk.RIGHT)
        
        # Options Frame
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # DPI Setting
        ttk.Label(options_frame, text="DPI:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Spinbox(options_frame, from_=72, to=600, textvariable=self.dpi, width=8).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Preview Frame
        self.preview_frame = ttk.LabelFrame(main_frame, text="Preview", padding="10")
        self.preview_frame.pack(fill=tk.BOTH, expand=True)
        
        self.preview_label = ttk.Label(self.preview_frame, text="No PDF selected", anchor=tk.CENTER)
        self.preview_label.pack(fill=tk.BOTH, expand=True)
        
        # Progress Bar
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Status Bar
        status_bar = ttk.Frame(main_frame)
        status_bar.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(status_bar, textvariable=self.status, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.convert_btn = ttk.Button(button_frame, text="Convert to PNG", command=self.start_conversion)
        self.convert_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(button_frame, text="Exit", command=self.root.quit).pack(side=tk.RIGHT)
        
        # Bind events
        self.pdf_path.trace_add('write', self.update_preview)
    
    def browse_pdf(self):
        if self.conversion_in_progress:
            return
            
        file_path = filedialog.askopenfilename(
            title="Select PDF File",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        if file_path:
            self.pdf_path.set(file_path)
            # Set default output directory to same as PDF if not set
            if not self.output_dir.get():
                self.output_dir.set(str(Path(file_path).parent / "output"))
    
    def browse_output_dir(self):
        if self.conversion_in_progress:
            return
            
        dir_path = filedialog.askdirectory(
            title="Select Output Directory"
        )
        if dir_path:
            self.output_dir.set(dir_path)
    
    def update_preview(self, *args):
        pdf_path = self.pdf_path.get()
        if not pdf_path or not os.path.exists(pdf_path):
            self.preview_label.config(text="No PDF selected")
            return
        
        try:
            # Show loading message
            self.preview_label.config(text="Loading preview...")
            self.root.update()
            
            # Load first page as preview
            images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=100)
            if images:
                # Resize image to fit in preview
                img = images[0]
                width, height = img.size
                max_size = 300
                if width > max_size or height > max_size:
                    ratio = min(max_size/width, max_size/height)
                    new_size = (int(width * ratio), int(height * ratio))
                    img = img.resize(new_size, Image.LANCZOS)
                
                # Convert to PhotoImage for Tkinter
                photo = ImageTk.PhotoImage(img)
                self.preview_label.config(image=photo)
                self.preview_label.image = photo  # Keep a reference!
            else:
                self.preview_label.config(text="Could not load preview")
                
        except Exception as e:
            self.preview_label.config(text=f"Error loading preview: {str(e)}")
    
    def start_conversion(self):
        if self.conversion_in_progress:
            return
            
        pdf_path = self.pdf_path.get()
        output_dir = self.output_dir.get()
        
        if not pdf_path or not os.path.exists(pdf_path):
            messagebox.showerror("Error", "Please select a valid PDF file.")
            return
            
        if not output_dir:
            messagebox.showerror("Error", "Please select an output directory.")
            return
            
        # Start conversion in a separate thread
        self.conversion_in_progress = True
        self.convert_btn.config(state=tk.DISABLED)
        self.status.set("Converting...")
        self.progress.set(0)
        
        thread = threading.Thread(
            target=self.convert_pdf,
            args=(pdf_path, output_dir, self.dpi.get())
        )
        thread.daemon = True
        thread.start()
        
        # Check thread status periodically
        self.check_thread(thread)
    
    def check_thread(self, thread):
        if thread.is_alive():
            self.root.after(100, lambda: self.check_thread(thread))
        else:
            self.conversion_in_progress = False
            self.convert_btn.config(state=tk.NORMAL)
            self.progress.set(100)
    
    def convert_pdf(self, pdf_path: str, output_dir: str, dpi: int):
        try:
            # Create output directory if it doesn't exist
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Get PDF info
            self.root.after(0, lambda: self.status.set("Loading PDF..."))
            
            # Convert PDF to images
            self.root.after(0, lambda: self.status.set("Converting pages..."))
            images = convert_from_path(pdf_path, dpi=dpi)
            
            # Save each page
            base_name = Path(pdf_path).stem
            total_pages = len(images)
            
            for i, image in enumerate(images, 1):
                output_file = output_path / f"{base_name}_page_{i:03d}.png"
                image.save(output_file, 'PNG')
                
                # Update progress
                progress = (i / total_pages) * 100
                self.root.after(0, self.progress.set, progress)
                self.root.after(0, self.status.set, f"Converting page {i} of {total_pages}...")
            
            self.root.after(0, lambda: self.status.set(f"Conversion complete! Saved {total_pages} images."))
            messagebox.showinfo("Success", f"Successfully converted {total_pages} pages to PNG.")
            
        except Exception as e:
            self.root.after(0, lambda: self.status.set("Error during conversion"))
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to convert PDF: {str(e)}"))
        finally:
            self.root.after(0, lambda: setattr(self, 'conversion_in_progress', False))
            self.root.after(0, lambda: self.convert_btn.config(state=tk.NORMAL))

def main():
    root = tk.Tk()
    app = PDFToPNGConverterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
