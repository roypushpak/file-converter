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
        
        # Drag and drop variables
        self.drag_start_index = None
        self.drag_current_index = None
        self.drag_y = 0
        self.drag_item = None
        self.drag_rect = None
        
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
        ttk.Button(button_frame, text="Remove All", command=self.remove_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Move Up", command=lambda: self.move_item(-1)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Move Down", command=lambda: self.move_item(1)).pack(side=tk.LEFT, padx=5)
        
        # Create a paned window to allow resizing between list and preview
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Left frame for image list
        list_frame = ttk.LabelFrame(paned, text="Selected Images (drag to reorder)", padding=5)
        paned.add(list_frame, weight=40)  # 40% of the width
        
        # Right frame for preview
        preview_frame = ttk.LabelFrame(paned, text="Preview", padding=5)
        paned.add(preview_frame, weight=60)  # 60% of the width
        
        # Create listbox with scrollbar for images
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(
            list_container,
            selectmode=tk.EXTENDED,
            exportselection=False,
            yscrollcommand=scrollbar.set
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        # Bind window resize event to update preview
        self.root.bind('<Configure>', lambda e: self.on_window_configure())
        
        # Preview area
        self.preview_canvas = tk.Canvas(preview_frame, bg='white', highlightthickness=0)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add a label for preview instructions
        self.preview_label = ttk.Label(
            self.preview_canvas,
            text="No image selected",
            background='white',
            foreground='gray',
            font=('Arial', 10, 'italic')
        )
        self.preview_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Bind events for drag and drop
        self.listbox.bind('<<ListboxSelect>>', self.on_select_change)
        self.listbox.bind('<Button-1>', self.on_mouse_down)
        self.listbox.bind('<B1-Motion>', self.on_mouse_move)
        self.listbox.bind('<ButtonRelease-1>', self.on_mouse_up)
        
        # Initialize drag state
        self.drag_start_y = 0
        self.drag_start_index = -1
        self.drag_item = None
        
        # Preview update method remains the same but will work with the new preview_canvas
        
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
    
    def remove_all(self):
        """Remove all images from the list."""
        if self.conversion_in_progress or not self.image_paths:
            return
            
        if messagebox.askyesno(
            "Remove All Images",
            "Are you sure you want to remove all images?"
        ):
            self.listbox.delete(0, tk.END)
            self.image_paths.clear()
            self.update_output_filename()
            self.update_status("Removed all images")
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
    
    def on_mouse_down(self, event):
        # Check if this is a left-click on an item
        if event.num == 1:  # Left mouse button
            index = self.listbox.nearest(event.y)
            if index >= 0:
                # Only start drag if we're not already dragging and it's a valid index
                if not hasattr(self, 'drag_start_index') or self.drag_start_index == -1:
                    self.drag_start_y = event.y
                    self.drag_start_index = index
                    self.drag_item = self.listbox.get(index)
                    
                    # Select the clicked item
                    self.listbox.selection_clear(0, tk.END)
                    self.listbox.selection_set(index)
                    self.listbox.activate(index)
                    
                    # Update preview immediately on click
                    self.current_preview_index = index
                    self.show_preview()
    
    def on_mouse_move(self, event):
        # Only process if we're in a drag operation
        if not hasattr(self, 'drag_start_index') or self.drag_start_index == -1:
            return
            
        # Calculate movement
        delta = event.y - self.drag_start_y
        if abs(delta) > 5:  # Only start dragging after a small movement
            # Get the current index under the mouse
            current_index = self.listbox.nearest(event.y)
            
            # Only process if we have a valid index that's different from start
            if 0 <= current_index < self.listbox.size() and current_index != self.drag_start_index:
                # Move the item in the list
                self.image_paths.insert(current_index, self.image_paths.pop(self.drag_start_index))
                
                # Update the listbox
                items = list(self.listbox.get(0, tk.END))
                item_text = items.pop(self.drag_start_index)
                items.insert(current_index, item_text)
                
                # Update the listbox
                self.listbox.delete(0, tk.END)
                for item in items:
                    self.listbox.insert(tk.END, item)
                
                # Update the drag start index
                self.drag_start_index = current_index
                
                # Update selection and ensure visibility
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(current_index)
                self.listbox.see(current_index)
                
                # Update preview to follow the dragged item
                if self.current_preview_index >= 0:
                    if self.current_preview_index == self.drag_start_index:
                        self.current_preview_index = current_index
                    elif (self.drag_start_index < self.current_preview_index <= current_index or
                          current_index <= self.current_preview_index < self.drag_start_index):
                        self.current_preview_index += (1 if self.drag_start_index < current_index else -1)
                    
                    # Update the preview
                    self.show_preview()
    
    def on_mouse_up(self, event):
        # Reset drag state on mouse up
        if hasattr(self, 'drag_start_index') and self.drag_start_index != -1:
            self.drag_start_index = -1
            self.drag_item = None
            
            # Force a selection change to update the preview if needed
            if self.listbox.curselection():
                index = self.listbox.curselection()[0]
                if 0 <= index < len(self.image_paths):
                    self.current_preview_index = index
                    self.show_preview()
    
    def on_window_configure(self, event=None):
        # Update preview when window is resized
        if hasattr(self, 'current_preview_index') and 0 <= self.current_preview_index < len(self.image_paths):
            self.root.after(100, self.show_preview)  # Small delay to allow window to finish resizing
    
    def on_select_change(self, event=None):
        print("\n--- on_select_change ---")  # Debug
        
        # Skip if we're in the middle of a drag operation
        if hasattr(self, 'drag_start_index') and self.drag_start_index != -1:
            print("Drag in progress, skipping preview update")
            return
            
        try:
            if not self.listbox.curselection():
                print("No selection")
                self.current_preview_index = -1
                self.show_preview()
                return
                
            selected_indices = self.listbox.curselection()
            print(f"Selected indices: {selected_indices}")
            
            if selected_indices:  # If there's any selection
                new_index = selected_indices[0]  # Take the first selected index
                print(f"New index: {new_index}, Current preview index: {self.current_preview_index}")
                
                if 0 <= new_index < len(self.image_paths):
                    self.current_preview_index = new_index
                    print(f"Requesting preview for index {new_index}")
                    self.show_preview()
                    
                    # Ensure the listbox maintains the selection
                    self.root.after(50, lambda: self._maintain_selection(new_index))
                else:
                    print(f"Index {new_index} out of range (0-{len(self.image_paths)-1})")
        except Exception as e:
            print(f"Error in on_select_change: {e}")
            import traceback
            traceback.print_exc()
    
    def _maintain_selection(self, index):
        """Helper to maintain selection after operations"""
        if 0 <= index < self.listbox.size():
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(index)
            self.listbox.activate(index)
    
    def show_preview(self):
        print("\n--- Starting show_preview ---")  # Debug
        print(f"Current preview index: {self.current_preview_index}")
        print(f"Number of images: {len(self.image_paths)}")
        
        # Clear previous preview if any
        if hasattr(self, 'preview_canvas'):
            self.preview_canvas.delete("all")
            self.preview_label.place_forget()
        
        # Check if we have a valid selection
        if not (0 <= self.current_preview_index < len(self.image_paths)):
            print("No valid image selected")
            if hasattr(self, 'preview_label'):
                self.preview_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            return
        
        try:
            image_path = self.image_paths[self.current_preview_index]
            print(f"Loading image: {image_path}")
            
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Open and convert the image with better quality settings
            with Image.open(image_path) as img:
                print(f"Original image size: {img.size}")
                
                # Convert to RGB if needed (for PNG with transparency)
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Get canvas dimensions with a safety check
                if not hasattr(self, 'preview_canvas'):
                    print("Preview canvas not initialized yet")
                    return
                    
                # Get available space with padding
                padding = 40
                canvas_width = max(10, self.preview_canvas.winfo_width() - padding * 2)
                canvas_height = max(10, self.preview_canvas.winfo_height() - padding * 2)
                
                print(f"Available canvas size: {canvas_width}x{canvas_height}")
                
                # Calculate new size maintaining aspect ratio with high quality
                width, height = img.size
                if width == 0 or height == 0:
                    raise ValueError("Invalid image dimensions (0x0)")
                
                # Calculate the maximum size that fits in the canvas while maintaining aspect ratio
                # Use a higher quality scaling factor for the initial resize
                scale_factor = min(canvas_width / width, canvas_height / height, 1.0)
                
                # For better quality, we'll do a two-pass resize for large downscaling
                if scale_factor < 0.5:  # If scaling down significantly
                    # First pass: resize to 2x target size for better quality
                    temp_size = (int(width * scale_factor * 2), int(height * scale_factor * 2))
                    if all(dim > 0 for dim in temp_size):
                        img = img.resize(temp_size, Image.LANCZOS)
                
                # Final resize to target size
                new_size = (max(1, int(width * scale_factor)), max(1, int(height * scale_factor)))
                print(f"Resizing to: {new_size} (original: {width}x{height})")
                
                # Apply high-quality resizing
                img = img.resize(new_size, Image.LANCZOS)
                
                # Apply a slight sharpening to enhance details
                # img = img.filter(ImageFilter.UnsharpMask(radius=0.5, percent=50, threshold=3))
                
                # Convert to PhotoImage with better quality settings
                photo = ImageTk.PhotoImage(
                    image=img,
                    master=self.preview_canvas
                )
                print("Image converted to PhotoImage")
                
                # Calculate position to center the image with padding
                x = (self.preview_canvas.winfo_width() - new_size[0]) // 2
                y = (self.preview_canvas.winfo_height() - new_size[1]) // 2
                
                # Ensure position is within canvas bounds
                x = max(padding // 2, min(x, self.preview_canvas.winfo_width() - new_size[0] - padding // 2))
                y = max(padding // 2, min(y, self.preview_canvas.winfo_height() - new_size[1] - padding // 2))
                
                print(f"Placing image at: ({x}, {y})")
                
                # Clear previous image and draw new one with a subtle shadow
                self.preview_canvas.delete("all")
                
                # Add a subtle background for transparent images
                bg_color = '#f0f0f0' if self.preview_canvas['bg'] == 'white' else '#404040'
                self.preview_canvas.create_rectangle(
                    x-1, y-1, 
                    x + new_size[0] + 1, 
                    y + new_size[1] + 1,
                    fill=bg_color, outline=bg_color
                )
                
                # Draw the image
                img_id = self.preview_canvas.create_image(x, y, anchor=tk.NW, image=photo)
                
                # Keep a reference to the image to prevent garbage collection
                self.preview_canvas.photo = photo
                
                # Draw a subtle border
                self.preview_canvas.create_rectangle(
                    x, y, 
                    x + new_size[0] - 1, 
                    y + new_size[1] - 1,
                    outline='#cccccc', width=1
                )
                
                # Update status with more info
                file_size = os.path.getsize(image_path) / 1024  # Size in KB
                status_text = f"Preview: {os.path.basename(image_path)} ({width}×{height}, {file_size:.1f} KB)"
                print(status_text)
                self.update_status(status_text)
                
        except Exception as e:
            error_msg = f"Error loading preview: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            if hasattr(self, 'preview_label'):
                self.preview_label.config(text=error_msg)
                self.preview_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    
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
