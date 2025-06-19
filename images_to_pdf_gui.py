#!/usr/bin/env python3
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from PIL import Image, ImageTk
import threading
from typing import List, Tuple

class ImagesToPDFConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Images to PDF Converter")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        
        # Variables
        self.image_paths: List[str] = []
        self.output_pdf = tk.StringVar()
        self.status = tk.StringVar(value="Ready")
        self.conversion_in_progress = False
        self.current_preview_index = -1
        
        self.setup_ui()
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top frame for buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Buttons
        ttk.Button(button_frame, text="Add Images", command=self.add_images).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Remove Selected", command=self.remove_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Move Up", command=lambda: self.move_item(-1)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Move Down", command=lambda: self.move_item(1)).pack(side=tk.LEFT, padx=5)
        
        # Listbox for images
        list_frame = ttk.LabelFrame(main_frame, text="Selected Images", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind selection change
        self.listbox.bind('<<ListboxSelect>>', self.on_select_change)
        
        # Preview frame
        self.preview_frame = ttk.LabelFrame(main_frame, text="Preview", padding="10")
        self.preview_frame.pack(fill=tk.BOTH, expand=True)
        
        self.preview_label = ttk.Label(self.preview_frame, text="No image selected", anchor=tk.CENTER)
        self.preview_label.pack(fill=tk.BOTH, expand=True)
        
        # Output file selection
        output_frame = ttk.Frame(main_frame)
        output_frame.pack(fill=tk.X, pady=(10, 5))
        
        ttk.Label(output_frame, text="Output PDF:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(output_frame, textvariable=self.output_pdf).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(output_frame, text="Browse...", command=self.browse_output).pack(side=tk.LEFT)
        
        # Status bar and Convert button
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(bottom_frame, textvariable=self.status, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.convert_btn = ttk.Button(bottom_frame, text="Convert to PDF", command=self.start_conversion)
        self.convert_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Set initial output filename
        self.update_output_filename()
    
    def add_images(self):
        if self.conversion_in_progress:
            return
            
        file_types = [
            ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.gif"),
            ("All files", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=file_types
        )
        
        if files:
            for file_path in files:
                if file_path not in self.image_paths:
                    self.image_paths.append(file_path)
                    self.listbox.insert(tk.END, os.path.basename(file_path))
            
            self.update_output_filename()
            self.update_status(f"Added {len(files)} image(s)")
    
    def remove_selected(self):
        if self.conversion_in_progress or not self.listbox.curselection():
            return
            
        # Get selected indices and sort in reverse order to avoid index shifting
        selected = sorted(self.listbox.curselection(), reverse=True)
        
        for index in selected:
            self.listbox.delete(index)
            self.image_paths.pop(index)
        
        self.update_output_filename()
        self.update_status(f"Removed {len(selected)} image(s)")
        self.preview_label.config(text="No image selected")
        self.current_preview_index = -1
    
    def move_item(self, direction):
        if self.conversion_in_progress or not self.listbox.curselection():
            return
            
        selected = self.listbox.curselection()
        if not selected:
            return
            
        index = selected[0]
        new_index = index + direction
        
        # Check if move is valid
        if new_index < 0 or new_index >= len(self.image_paths):
            return
        
        # Swap items in both listbox and image_paths
        self.image_paths[index], self.image_paths[new_index] = self.image_paths[new_index], self.image_paths[index]
        
        # Update listbox
        item1 = self.listbox.get(index)
        item2 = self.listbox.get(new_index)
        self.listbox.delete(index, index)
        self.listbox.insert(index, item2)
        self.listbox.delete(new_index, new_index)
        self.listbox.insert(new_index, item1)
        
        # Update selection
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(new_index)
        self.listbox.see(new_index)
        
        # Update preview if needed
        if self.current_preview_index == index or self.current_preview_index == new_index:
            self.current_preview_index = new_index
            self.show_preview()
    
    def on_select_change(self, event):
        if not self.listbox.curselection():
            return
            
        index = self.listbox.curselection()[0]
        if 0 <= index < len(self.image_paths) and index != self.current_preview_index:
            self.current_preview_index = index
            self.show_preview()
    
    def show_preview(self):
        if self.current_preview_index < 0 or self.current_preview_index >= len(self.image_paths):
            self.preview_label.config(text="No image selected")
            return
            
        try:
            image_path = self.image_paths[self.current_preview_index]
            img = Image.open(image_path)
            
            # Resize image to fit in preview
            width, height = img.size
            max_size = 400
            if width > max_size or height > max_size:
                ratio = min(max_size/width, max_size/height)
                new_size = (int(width * ratio), int(height * ratio))
                img = img.resize(new_size, Image.LANCZOS)
            
            # Convert to PhotoImage for Tkinter
            photo = ImageTk.PhotoImage(img)
            self.preview_label.config(image=photo)
            self.preview_label.image = photo  # Keep a reference!
            
            # Update status
            self.update_status(f"Preview: {os.path.basename(image_path)} ({width}x{height})")
            
        except Exception as e:
            self.preview_label.config(text=f"Error loading preview: {str(e)}")
    
    def browse_output(self):
        if self.conversion_in_progress:
            return
            
        initial_dir = os.path.dirname(self.output_pdf.get()) if self.output_pdf.get() else None
        file_path = filedialog.asksaveasfilename(
            title="Save PDF As",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")],
            initialdir=initial_dir,
            initialfile=os.path.basename(self.output_pdf.get() or "output.pdf")
        )
        
        if file_path:
            self.output_pdf.set(file_path)
    
    def update_output_filename(self):
        if not self.image_paths:
            self.output_pdf.set("")
            return
            
        # Use the directory of the first image
        first_image = Path(self.image_paths[0])
        default_name = first_image.parent / f"{first_image.stem}_combined.pdf"
        self.output_pdf.set(str(default_name))
    
    def update_status(self, message: str):
        self.status.set(message)
    
    def start_conversion(self):
        if self.conversion_in_progress or not self.image_paths or not self.output_pdf.get():
            return
            
        output_path = self.output_pdf.get()
        
        # Check if output directory exists
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except OSError as e:
                messagebox.showerror("Error", f"Cannot create output directory: {str(e)}")
                return
        
        # Start conversion in a separate thread
        self.conversion_in_progress = True
        self.convert_btn.config(state=tk.DISABLED)
        self.update_status("Converting to PDF...")
        
        thread = threading.Thread(
            target=self.convert_to_pdf,
            args=(self.image_paths, output_path)
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
    
    def convert_to_pdf(self, image_paths: List[str], output_path: str):
        try:
            # Convert all images to RGB mode (required for PDF)
            images = []
            for i, img_path in enumerate(image_paths, 1):
                try:
                    img = Image.open(img_path)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    images.append(img)
                    self.root.after(0, lambda i=i: self.update_status(f"Processing image {i}/{len(image_paths)}"))
                except Exception as e:
                    self.root.after(0, lambda e=e, p=img_path: messagebox.showwarning(
                        "Warning", 
                        f"Could not process {os.path.basename(p)}: {str(e)}"
                    ))
            
            if not images:
                self.root.after(0, lambda: messagebox.showerror("Error", "No valid images to convert"))
                return
            
            # Save first image as PDF and append the rest
            if len(images) == 1:
                images[0].save(output_path, "PDF", resolution=100.0)
            else:
                images[0].save(
                    output_path, 
                    "PDF", 
                    resolution=100.0,
                    save_all=True,
                    append_images=images[1:]
                )
            
            self.root.after(0, lambda: self.update_status(f"Successfully created {os.path.basename(output_path)}"))
            self.root.after(0, lambda: messagebox.showinfo(
                "Success", 
                f"Successfully created PDF with {len(images)} pages\n\nSaved to:\n{output_path}"
            ))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to create PDF: {str(e)}"))
            self.root.after(0, lambda: self.update_status("Conversion failed"))
        finally:
            # Close all images
            for img in images:
                try:
                    img.close()
                except:
                    pass

def main():
    root = tk.Tk()
    app = ImagesToPDFConverterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
