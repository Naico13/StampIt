import os
import shutil
import uuid
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageDraw
from stamp_app.src.image_processing import detect_and_segment_stamps
from stamp_app.src.db_utils import get_stamp_by_image_path, initialize_database # Added
#sxvcscx

# Main application script for the stamp scanner app.
# This file will contain the core logic for the application.
# It will orchestrate the image processing, web retrieval, and database interactions.

# Define the base directory of the application
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADED_IMAGES_DIR = BASE_DIR / "data" / "uploaded_images"
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}

# Ensure UPLOADED_IMAGES_DIR exists at startup
UPLOADED_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

def handle_image_upload(image_path: str) -> str:
    """
    Handles the upload of an image file. (Content from previous step, unchanged)
    Validates the image file, creates a unique filename, copies it to the
    'uploaded_images' directory, and returns the path to the saved image.
    Args:
        image_path: The path to the image file on the local system.
    Returns:
        The full path to the newly saved image in the 'uploaded_images' directory.
    Raises:
        FileNotFoundError: If the image_path does not point to an existing file.
        ValueError: If the file is not a recognized image type (based on extension)
                    or if the target directory cannot be created.
        IOError: If an error occurs during file copying.
    """
    source_path = Path(image_path)
    if not source_path.is_file():
        raise FileNotFoundError(f"Source image file not found at: {image_path}")
    if source_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Invalid image file type: {source_path.suffix}. "
            f"Allowed types are: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    target_dir = UPLOADED_IMAGES_DIR # Already created at startup
    unique_filename = f"{source_path.stem}_{uuid.uuid4().hex}{source_path.suffix}"
    destination_path = target_dir / unique_filename
    try:
        shutil.copy2(source_path, destination_path)
    except IOError as e:
        raise IOError(f"Error copying file from {source_path} to {destination_path}: {e}")
    return str(destination_path)


class StampScannerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Stamp Scanner Application")
        self.geometry("800x600") # Default size

        self.current_image_path = None # Path to the image in uploaded_images/
        self.original_selected_path = None # Path to the image selected by user
        self.original_pil_image = None # To store the pristine loaded image
        self.tk_image_with_rects = None # To store image with rectangles
        self.detected_stamps_data = [] # List of {'path': '...', 'bbox': (x,y,w,h)}
        self.displayed_stamp_rects_info = [] # List of {'scaled_bbox': (x1,y1,x2,y2), 'original_data': ...}

        # --- UI Elements ---
        # Top frame for buttons
        top_frame = ttk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # Detect Stamps Button
        self.detect_button = ttk.Button(
            top_frame, text="Detect Stamps", command=self.run_stamp_detection, state=tk.DISABLED
        )
        self.detect_button.pack(side=tk.LEFT)

        # Menu
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open Image", command=self.open_image_dialog)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        self.config(menu=menubar)

        # Main content frame
        content_frame = ttk.Frame(self, padding="10")
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Image display area
        self.image_label = ttk.Label(content_frame, text="No image selected.")
        self.image_label.pack(pady=10, fill=tk.BOTH, expand=True)
        self.image_label.bind("<Button-1>", self.on_image_click) # Bind click event
        
        # Status bar
        self.status_bar = ttk.Label(self, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        initialize_database() # Initialize DB at startup

    def open_image_dialog(self):
        """
        Opens a file dialog for the user to select an image.
        If an image is selected, it's processed and displayed.
        """
        # Clear previous detection results
        self.detected_stamps_data = []
        self.displayed_stamp_rects_info = []
        
        self.status_bar.config(text="Opening file dialog...")
        filetypes = (("Image files", "*.jpg *.jpeg *.png"), ("All files", "*.*"))
        filepath = filedialog.askopenfilename(
            title="Select an Image", filetypes=filetypes
        )

        if not filepath:
            self.status_bar.config(text="File selection cancelled.")
            self.detect_button.config(state=tk.DISABLED) # Disable if no file
            return

        self.original_selected_path = filepath
        self.status_bar.config(text=f"Selected: {os.path.basename(filepath)}")

        try:
            self.current_image_path = handle_image_upload(filepath)
            self.status_bar.config(text=f"Image processed: {os.path.basename(self.current_image_path)}")
            
            self.display_image(self.current_image_path) # This will now enable the button
            # self.detect_button.config(state=tk.NORMAL) # Moved to display_image

        except FileNotFoundError as e:
            messagebox.showerror("Error", f"File not found: {e}")
            self.status_bar.config(text="Error: File not found.")
            self.detect_button.config(state=tk.DISABLED)
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid file: {e}")
            self.status_bar.config(text="Error: Invalid file.")
            self.detect_button.config(state=tk.DISABLED)
        except IOError as e:
            messagebox.showerror("Error", f"Could not read or copy image: {e}")
            self.status_bar.config(text="Error: Could not read/copy image.")
            self.detect_button.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            self.status_bar.config(text="Error: Unexpected error.")
            self.detect_button.config(state=tk.DISABLED)

    def display_image(self, image_path_to_display, draw_boxes_on_this_image=None):
        """
        Loads an image, optionally draws boxes, scales, and displays it.
        If draw_boxes_on_this_image is provided, it's used as the base for drawing.
        Otherwise, image_path_to_display is loaded.
        """
        try:
            if draw_boxes_on_this_image:
                # We are displaying an image already in memory (likely with boxes)
                # The original_pil_image should already be set from initial load.
                display_pil_image = draw_boxes_on_this_image 
            else:
                # This is a fresh load (e.g., after open_image_dialog or clearing boxes)
                self.original_pil_image = Image.open(image_path_to_display)
                display_pil_image = self.original_pil_image.copy()

            self.image_label.update_idletasks()
            label_width = self.image_label.winfo_width()
            label_height = self.image_label.winfo_height()

            if label_width <= 1 or label_height <= 1:
                label_width, label_height = 600, 400 # Default reasonable size for first display

            img_width, img_height = display_pil_image.size
            aspect_ratio = img_width / img_height
            
            new_width = label_width
            new_height = int(new_width / aspect_ratio)
            if new_height > label_height:
                new_height = label_height
                new_width = int(new_height * aspect_ratio)
            
            new_width = max(1, new_width)
            new_height = max(1, new_height)

            resized_image = display_pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Store the scaled dimensions and factors if needed elsewhere,
            # but for drawing, we'll scale within draw_stamp_rectangles.
            # self.scaled_image_width = new_width 
            # self.scaled_image_height = new_height

            self.tk_image = ImageTk.PhotoImage(resized_image)
            self.image_label.config(image=self.tk_image, text="")
            self.image_label.image = self.tk_image
            
            if not draw_boxes_on_this_image: # Only for initial display or revert
                 self.status_bar.config(text=f"Displayed: {os.path.basename(image_path_to_display)}")
            
            if hasattr(self, 'detect_button'): # Ensure button exists
                self.detect_button.config(state=tk.NORMAL if self.current_image_path else tk.DISABLED)

        except FileNotFoundError:
            messagebox.showerror("Error", f"Image file not found at: {image_path_to_display}")
            self.image_label.config(image="", text="Error: Image not found.")
            self.status_bar.config(text="Error: Image not found for display.")
            if hasattr(self, 'detect_button'): self.detect_button.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to display image: {e}")
            self.image_label.config(image="", text=f"Error displaying image: {e}")
            self.status_bar.config(text="Error: Failed to display image.")
            if hasattr(self, 'detect_button'): self.detect_button.config(state=tk.DISABLED)

    def run_stamp_detection(self):
        if not self.current_image_path or not self.original_pil_image:
            messagebox.showerror("Error", "Please open an image first.")
            return
            
        # Clear previous results
        self.detected_stamps_data = []
        self.displayed_stamp_rects_info = []

        self.status_bar.config(text="Detecting stamps...")
        self.update_idletasks() # Ensure status bar updates

        try:
            detected_stamps_data_result = detect_and_segment_stamps(self.current_image_path)
            self.detected_stamps_data = detected_stamps_data_result # Store full data

            if self.detected_stamps_data:
                # Pass the full data to draw_stamp_rectangles
                self.draw_stamp_rectangles(self.detected_stamps_data) 
                self.status_bar.config(text=f"{len(self.detected_stamps_data)} stamps detected.")
            else:
                self.status_bar.config(text="No stamps found.")
                self.display_image(self.current_image_path) 
                messagebox.showinfo("Detection Result", "No stamps were detected in the image.")

        except IOError as e: 
            messagebox.showerror("Detection Error", f"Error reading image for detection: {e}")
            self.status_bar.config(text="Detection error.")
        except ValueError as e: 
             messagebox.showerror("Detection Error", f"Configuration error during detection: {e}")
             self.status_bar.config(text="Detection error.")
        except Exception as e:
            messagebox.showerror("Detection Error", f"An unexpected error occurred during detection: {e}")
            self.status_bar.config(text="Detection error.")


    def draw_stamp_rectangles(self, stamps_data_to_draw): # Renamed param
        if not self.original_pil_image:
            messagebox.showerror("Error", "Original image not available for drawing.")
            return

        self.displayed_stamp_rects_info = [] # Clear old scaled rect info
        image_to_draw_on = self.original_pil_image.copy()
        draw = ImageDraw.Draw(image_to_draw_on)

        # Get current display dimensions for scaling bounding boxes
        # This is crucial for accurate click detection on the displayed image
        self.image_label.update_idletasks()
        label_width = self.image_label.winfo_width()
        label_height = self.image_label.winfo_height()

        if label_width <= 1 or label_height <= 1: # Should not happen if image is displayed
            label_width, label_height = self.image_label.master.winfo_width(), self.image_label.master.winfo_height()


        orig_img_width, orig_img_height = self.original_pil_image.size
        
        # Calculate scale factors based on how original_pil_image was scaled to fit label_width/label_height
        # This mirrors the logic in display_image's resizing
        aspect_ratio = orig_img_width / orig_img_height
        
        scaled_display_width = label_width
        scaled_display_height = int(scaled_display_width / aspect_ratio)
        if scaled_display_height > label_height:
            scaled_display_height = label_height
            scaled_display_width = int(scaled_display_height * aspect_ratio)
        
        scaled_display_width = max(1, scaled_display_width)
        scaled_display_height = max(1, scaled_display_height)

        scale_x = scaled_display_width / orig_img_width
        scale_y = scaled_display_height / orig_img_height

        for stamp_item in stamps_data_to_draw:
            x, y, w, h = stamp_item['bbox']
            
            # Draw on the copy of the original image (unscaled coordinates)
            draw.rectangle([(x, y), (x + w, y + h)], outline="red", width=2)
            
            # Calculate scaled coordinates for click detection
            # These are relative to the top-left of the image_label
            scaled_x1 = int(x * scale_x)
            scaled_y1 = int(y * scale_y)
            scaled_x2 = int((x + w) * scale_x)
            scaled_y2 = int((y + h) * scale_y)
            
            self.displayed_stamp_rects_info.append({
                'scaled_bbox': (scaled_x1, scaled_y1, scaled_x2, scaled_y2),
                'original_data': stamp_item 
            })
            
        self.display_image(self.current_image_path, draw_boxes_on_this_image=image_to_draw_on)

    def on_image_click(self, event):
        click_x, click_y = event.x, event.y
        
        # Adjust click coordinates if the image within the label is smaller than the label
        # (i.e., letterboxed or pillarboxed)
        self.image_label.update_idletasks()
        label_width = self.image_label.winfo_width()
        label_height = self.image_label.winfo_height()

        # Get the actual displayed image dimensions (scaled image)
        # This assumes self.tk_image holds the currently displayed ImageTk.PhotoImage object
        if not hasattr(self, 'tk_image') or self.tk_image is None:
            return 

        displayed_img_width = self.tk_image.width()
        displayed_img_height = self.tk_image.height()

        # Calculate offsets if image is centered in label
        offset_x = (label_width - displayed_img_width) // 2
        offset_y = (label_height - displayed_img_height) // 2

        adjusted_click_x = click_x - offset_x
        adjusted_click_y = click_y - offset_y

        for item_info in self.displayed_stamp_rects_info:
            scaled_x1, scaled_y1, scaled_x2, scaled_y2 = item_info['scaled_bbox']
            
            # Compare with adjusted click coordinates
            if scaled_x1 <= adjusted_click_x <= scaled_x2 and \
               scaled_y1 <= adjusted_click_y <= scaled_y2:
                
                original_stamp_data = item_info['original_data']
                detected_stamp_image_path = original_stamp_data['path']
                stamp_bbox = original_stamp_data['bbox']
                
                status_text = f"Clicked stamp: {os.path.basename(detected_stamp_image_path)} @ {stamp_bbox}. Fetching DB details..."
                self.status_bar.config(text=status_text)
                self.update_idletasks()

                stamp_details_from_db = get_stamp_by_image_path(detected_stamp_image_path)
                
                if stamp_details_from_db:
                    self.status_bar.config(text=f"Displaying details for: {os.path.basename(detected_stamp_image_path)}")
                else:
                    self.status_bar.config(text=f"No DB details for: {os.path.basename(detected_stamp_image_path)}")

                self.show_stamp_details_window(stamp_details_from_db, original_stamp_data)
                return # Found a click, no need to check others

        # If no rectangle was clicked, you might want to clear the status or specific info
        # self.status_bar.config(text="Clicked on image area.")

    def show_stamp_details_window(self, db_details, original_detection_data):
        details_window = tk.Toplevel(self)
        details_window.title(f"Stamp Details: {os.path.basename(original_detection_data['path'])}")
        details_window.geometry("500x600") # Adjusted size

        # Main frame in the new window
        main_details_frame = ttk.Frame(details_window, padding="10")
        main_details_frame.pack(fill=tk.BOTH, expand=True)

        # Frame for the image
        image_frame = ttk.Frame(main_details_frame)
        image_frame.pack(pady=10)
        
        try:
            pil_image = Image.open(original_detection_data['path'])
            img_width, img_height = pil_image.size
            max_dim = 200
            
            if img_width > max_dim or img_height > max_dim:
                aspect_ratio = img_width / img_height
                if img_width > img_height:
                    new_width = max_dim
                    new_height = int(new_width / aspect_ratio)
                else:
                    new_height = max_dim
                    new_width = int(new_height * aspect_ratio)
                pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            stamp_tk_image = ImageTk.PhotoImage(pil_image)
            image_detail_label = ttk.Label(image_frame, image=stamp_tk_image)
            image_detail_label.image = stamp_tk_image # Keep reference
            image_detail_label.pack()
        except FileNotFoundError:
            ttk.Label(image_frame, text="Cropped image not found.").pack()
        except Exception as e:
            ttk.Label(image_frame, text=f"Error loading image: {e}").pack()

        # Frame for textual details
        info_frame = ttk.Frame(main_details_frame)
        info_frame.pack(fill=tk.BOTH, expand=True)

        row_idx = 0
        
        def add_detail_row(label_text, value_text):
            nonlocal row_idx
            ttk.Label(info_frame, text=label_text, font=('Helvetica', 10, 'bold')).grid(row=row_idx, column=0, sticky=tk.W, padx=5, pady=2)
            
            # Use Text widget for potentially long values to allow scrolling and copying
            if isinstance(value_text, str) and len(value_text) > 70: # Heuristic for long text
                text_val_widget = tk.Text(info_frame, height=3, width=50, wrap=tk.WORD, relief=tk.FLAT, borderwidth=0)
                text_val_widget.insert(tk.END, value_text)
                text_val_widget.config(state=tk.DISABLED, highlightthickness=0) # Read-only, remove border
                text_val_widget.grid(row=row_idx, column=1, sticky=tk.EW, padx=5, pady=2)
            else:
                 ttk.Label(info_frame, text=str(value_text), wraplength=350).grid(row=row_idx, column=1, sticky=tk.W, padx=5, pady=2)
            row_idx += 1

        add_detail_row("File Path:", os.path.basename(original_detection_data['path']))
        add_detail_row("Original BBox:", str(original_detection_data['bbox']))

        if db_details:
            add_detail_row("DB ID:", db_details.get('id', 'N/A'))
            add_detail_row("Keywords:", db_details.get('search_keywords', 'N/A'))
            add_detail_row("Country:", db_details.get('country', 'N/A'))
            add_detail_row("Title Suggestion:", db_details.get('title_suggestion', 'N/A'))
            add_detail_row("Price Range:", db_details.get('estimated_price_range', 'N/A'))
            
            history = db_details.get('history_notes', 'N/A')
            add_detail_row("History:", history)

            source_urls_data = db_details.get('source_urls')
            if isinstance(source_urls_data, list) and source_urls_data: # Should be list from db_utils
                add_detail_row("Sources:", "\n".join(source_urls_data))
            elif isinstance(source_urls_data, str) and source_urls_data: # Fallback if it's a string
                 add_detail_row("Sources:", source_urls_data)
            else:
                add_detail_row("Sources:", "N/A")
        else:
            ttk.Label(info_frame, text="No further details found in the database for this stamp.", font=('Helvetica', 10, 'italic')).grid(row=row_idx, column=0, columnspan=2, sticky=tk.W, padx=5, pady=10)
            row_idx+=1
        
        info_frame.columnconfigure(1, weight=1) # Make value column expandable

        # Add a close button
        close_button = ttk.Button(main_details_frame, text="Close", command=details_window.destroy)
        close_button.pack(pady=10)

        details_window.transient(self) # Keep window on top of main
        details_window.grab_set()      # Modal behavior
        self.wait_window(details_window) # Wait until it's closed


def main():
    """
    Initializes and runs the Stamp Scanner Tkinter application.
    """
    app = StampScannerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
