import cv2
import numpy as np
import os
import uuid
from pathlib import Path

# This file will contain the logic for stamp detection from images.
# Functions for image loading, preprocessing, feature extraction,
# and stamp segmentation will be implemented here.

# Define the base directory of the application to resolve paths correctly
BASE_DIR = Path(__file__).resolve().parent.parent
DETECTED_STAMPS_DIR = BASE_DIR / "data" / "detected_stamps"

# Constants for contour filtering
MIN_CONTOUR_AREA = 1000  # Minimum area to be considered a potential stamp
MAX_CONTOUR_AREA = 50000 # Maximum area
ASPECT_RATIO_MIN = 0.5   # Minimum aspect ratio (width/height)
ASPECT_RATIO_MAX = 2.0   # Maximum aspect ratio


def detect_and_segment_stamps(uploaded_image_path: str) -> list[str]:
    """
    Detects and segments stamps from an uploaded image.

    The function reads an image, performs preprocessing (grayscale, blur, edge detection),
    finds contours, filters them to identify potential stamps, crops these stamps,
    and saves them to the 'data/detected_stamps/' directory.

    Args:
        uploaded_image_path: The path to the image file in
                             'stamp_app/data/uploaded_images/'.

    Returns:
        A list of full paths to the saved (cropped) stamp images.
        Returns an empty list if no stamps are detected or if an error occurs.

    Raises:
        IOError: If the image file cannot be read by OpenCV.
        ValueError: If the output directory cannot be created.
    """
    detected_stamp_paths = []
    source_image_path = Path(uploaded_image_path)

    # 1. Ensure output directory exists
    try:
        DETECTED_STAMPS_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        # Consider logging this error instead of raising if preferred
        # For now, raising helps signal a critical problem.
        raise ValueError(f"Could not create detected stamps directory {DETECTED_STAMPS_DIR}: {e}")

    # 2. Read the image
    img = cv2.imread(str(source_image_path))
    if img is None:
        # This is a common way to check if cv2.imread failed
        raise IOError(f"Failed to load image at path: {uploaded_image_path}. "
                      "Check if the file exists and is a valid image format.")

    original_image_for_cropping = img.copy() # Keep a copy for cropping later

    # 3. Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 4. Apply Gaussian blur
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # 5. Perform edge detection (Canny)
    # Adjust thresholds as needed; these are common starting points
    edges = cv2.Canny(blurred, 50, 150)

    # 6. Find contours
    # RETR_EXTERNAL retrieves only the extreme outer contours.
    # CHAIN_APPROX_SIMPLE compresses horizontal, vertical, and diagonal segments
    # and leaves only their end points.
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 7. Filter contours and process potential stamps
    processed_stamps_data = [] # Changed from detected_stamp_paths
    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)

        # Filter by area
        if MIN_CONTOUR_AREA < area < MAX_CONTOUR_AREA:
            # Approximate contour to a polygon
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True) # 0.02 is a common epsilon value

            # Check if the approximated contour is a quadrilateral
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx) # These are relative to the processed image (e.g., gray)
                                                      # but should be fine if no resizing was done before contour detection

                # Additional filter: aspect ratio of the bounding box
                aspect_ratio = float(w) / h
                if ASPECT_RATIO_MIN <= aspect_ratio <= ASPECT_RATIO_MAX:
                    # Crop the stamp from the original image (before any scaling for processing)
                    cropped_stamp = original_image_for_cropping[y : y + h, x : x + w]

                    # Create a unique filename
                    original_filename_stem = source_image_path.stem
                    unique_stamp_filename = f"{original_filename_stem}_stamp_{uuid.uuid4().hex[:8]}.png" # Save as PNG
                    stamp_save_path = DETECTED_STAMPS_DIR / unique_stamp_filename

                    # Save the cropped stamp
                    try:
                        cv2.imwrite(str(stamp_save_path), cropped_stamp)
                        processed_stamps_data.append({
                            'path': str(stamp_save_path),
                            'bbox': (x, y, w, h)  # Bounding box from the original image scale
                        })
                    except Exception as e: # Catch cv2.imwrite errors specifically if possible
                        # Log this error, but continue processing other contours
                        print(f"Warning: Could not save detected stamp {stamp_save_path}: {e}")

    return processed_stamps_data


def main_test():
    """
    Placeholder main function to test detect_and_segment_stamps.
    Assumes a sample image exists for testing.
    """
    print("Testing stamp detection and segmentation...")

    # In a real scenario, this image would come from the handle_image_upload function's output.
    # For testing, we need a placeholder image. Let's assume one exists in uploaded_images.
    # We will create a dummy image for this test to run in the sandbox.

    sample_image_dir = BASE_DIR / "data" / "uploaded_images"
    sample_image_dir.mkdir(parents=True, exist_ok=True)
    sample_image_name = "test_stamp_sheet.png"
    sample_image_path = sample_image_dir / sample_image_name

    # Create a simple dummy PNG image for testing if it doesn't exist
    if not sample_image_path.exists():
        try:
            # Create a small, simple black image with a white rectangle (our "stamp")
            dummy_img_data = np.zeros((300, 400, 3), dtype=np.uint8) # Black background
            cv2.rectangle(dummy_img_data, (50, 50), (150, 200), (255, 255, 255), -1) # White rectangle
            cv2.rectangle(dummy_img_data, (200, 80), (350, 180), (200, 200, 200), -1) # Another one
            cv2.imwrite(str(sample_image_path), dummy_img_data)
            print(f"Created dummy test image: {sample_image_path}")
        except Exception as e:
            print(f"Could not create dummy test image {sample_image_path}: {e}")
            return # Can't proceed if dummy image creation fails

    if not sample_image_path.is_file():
        print(f"Test image not found at {sample_image_path}. Please place a sample image there.")
        return

    print(f"Using sample image: {sample_image_path}")

    try:
        detected_stamps_data = detect_and_segment_stamps(str(sample_image_path))
        if detected_stamps_data:
            print(f"\nSuccessfully detected {len(detected_stamps_data)} stamp(s):")
            print("--------------------------------------------------------------------------------")
            print("Detected stamp data (use these paths for manual DB setup in db_utils.py):")
            for stamp_info in detected_stamps_data:
                # Make the path relative to the app's base directory for easier use
                try:
                    relative_path = Path(stamp_info['path']).relative_to(BASE_DIR)
                    print(f"  - Path: {relative_path}, BBox: {stamp_info['bbox']}")
                except ValueError: # If path is not relative to BASE_DIR for some reason
                    print(f"  - Path: {stamp_info['path']} (Absolute), BBox: {stamp_info['bbox']}")
            print("--------------------------------------------------------------------------------\n")
        else:
            print("No stamps were detected in the sample image.")
    except IOError as e:
        print(f"Error reading image: {e}")
    except ValueError as e:
        print(f"Configuration error: {e}")
    except Exception as e: # Catch any other unexpected errors during processing
        print(f"An unexpected error occurred during stamp detection: {e}")
    finally:
        # Optional: Clean up the dummy image after test
        # if sample_image_path.exists() and "test_stamp_sheet.png" in str(sample_image_path): # Basic safety check
        #     try:
        #         sample_image_path.unlink()
        #         print(f"Cleaned up dummy test image: {sample_image_path}")
        #     except OSError as e:
        #         print(f"Error cleaning up dummy test image {sample_image_path}: {e}")
        pass


if __name__ == "__main__":
    # This allows running the test function directly if the script is executed.
    # Note: In a real application, this script would typically be imported as a module.
    main_test()
