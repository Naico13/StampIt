# StampScannerApp

## Description

StampScannerApp is an iOS application designed to help users digitize their stamp collections. Users can import photos of their stamp album pages, and the app will attempt to detect individual stamps within these images. Tapping on a detected stamp allows users to fetch and view (currently mock) detailed information about it, including its origin, history, and estimated market value.

## Features

*   **Photo Library Import:** Import images of stamp album pages directly from the user's Photo Library.
*   **Image Gallery & Detail View:**
    *   Display imported images in a scrollable gallery view.
    *   Tap an image to open a detailed view.
*   **Image Management:**
    *   Rename imported images.
    *   Delete images from the app.
*   **Stamp Detection:**
    *   Utilizes Apple's Vision framework (`VNDetectRectanglesRequest`) to detect rectangular shapes (interpreted as stamps) within the imported images.
    *   Draws bounding boxes around these detected stamps in the image detail view.
*   **Interactive Stamp Information (Mock Data):**
    *   Tap on a detected bounding box to trigger a fetch for information about that specific stamp.
    *   Displays (mock) estimated market value as a text overlay near the bounding box.
    *   Bounding boxes are color-coded based on the (mock) estimated market value (e.g., grey for unknown/low, yellow for higher value).
    *   Presents a detailed sheet view with comprehensive (mock) information about the selected stamp, including name, country, date of issuance, rarity, history, etc.
*   **Persistence:**
    *   Image metadata (name, timestamp, detected bounding box coordinates) is saved to a JSON file in the app's documents directory.
    *   Imported images are saved as JPEG files in the app's documents directory.

## Project Structure

*   **Platform:** iOS
*   **Language:** Swift
*   **UI Framework:** SwiftUI
*   **Core Technologies:**
    *   **Vision Framework:** Used for detecting rectangular objects (stamps) in images.
    *   **PhotosUI Framework:** Used for image picking from the Photo Library (`PHPickerViewController`).
*   **Data Storage:**
    *   Image files are stored directly in the app's documents directory.
    *   Metadata associated with each image (including bounding boxes for detected stamps) is persisted in a JSON file (`images.json`) within the documents directory.

## Current Limitations / Future Work

This application provides a foundational framework for a stamp scanning and cataloging tool. Key areas for future development include:

*   **Real Stamp Data Integration:**
    *   The current stamp information (name, value, history, etc.) is entirely **mocked** via `StampInfoService.swift`.
    *   **Future Work:** Integrate with a real stamp database API (e.g., Colnect, StampWorld API if available) or develop a web scraping solution to fetch authentic stamp details.
*   **Advanced Stamp Detection Model:**
    *   The app currently uses Vision's general `VNDetectRectanglesRequest`, which may not be accurate for all types of stamps (e.g., non-rectangular, heavily postmarked, or on complex backgrounds).
    *   **Future Work:** Train a custom Core ML model specifically for stamp detection (using `VNRecognizeObjectsRequest` or `VNCoreMLRequest`) to improve accuracy and reliability across a wider variety of stamps.
*   **Camera Input:**
    *   The app currently only supports importing images from the Photo Library.
    *   **Future Work:** Implement direct image capture using the device camera (`AVFoundation` or `UIImagePickerController` for camera source type).
*   **Error Handling & UI Refinements:**
    *   **Image File I/O Errors:** While metadata saving/loading has improved error handling, saving individual image files (in `ImageModel.init`) and deleting them (`ContentView.deleteImageFromFileSystem`) should more robustly propagate errors to the user (e.g., via alerts).
    *   **Image Cropping Failure Alert:** If cropping a detected stamp region fails in `ImageDetailView`, the user should be alerted, as identification accuracy might be affected when falling back to the full image.
    *   **Loading Indicators:** Provide more granular visual feedback during operations like fetching stamp information for a specific tapped box in `ImageDetailView`.
    *   **Asynchronous Image File I/O:** For very large images or to further improve UI responsiveness, consider moving all image file read/write operations to background threads or an actor system.
    *   **Thumbnail Caching:** Implement on-disk caching for thumbnails to avoid re-generating them on each app launch, further improving `ContentView` performance.
*   **User Accounts & Cloud Sync:**
    *   **Future Work:** Allow users to create accounts and sync their stamp collection data across multiple devices using iCloud or another cloud backend.
*   **Advanced Collection Management:**
    *   **Future Work:** Features like manual data entry for stamps, sorting/filtering the collection, adding custom notes, and tracking purchase/sale information.

This README provides an overview of the StampScannerApp, its current capabilities, and potential avenues for future enhancement.
