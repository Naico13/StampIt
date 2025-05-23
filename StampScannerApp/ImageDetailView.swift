//
//  ImageDetailView.swift
//  StampScannerApp
//
//  Created by [Your Name]
//  Copyright © [Year] [Your Organization]. All rights reserved.
//
//  This file defines the view for displaying an individual imported image,
//  allowing users to see detected stamps, fetch information about them,
//  rename the image, or delete it.
//

import SwiftUI
import Vision // For VNRectangleObservation, though CGRect is CoreGraphics

/// A view that displays an individual image, its detected stamps (as bounding boxes),
/// and allows interaction with these elements. Users can rename or delete the image,
//  re-detect stamps, and tap on detected stamps to get more information.
struct ImageDetailView: View {
    /// Environment variable to control the presentation state of this view (e.g., for dismissing it).
    @Environment(\.presentationMode) var presentationMode
    
    /// The `ImageModel` instance being displayed and potentially modified.
    @State var imageModel: ImageModel
    
    /// State variable to control the visibility of the rename alert.
    @State private var showingRenameAlert = false
    /// State variable to hold the new name entered by the user in the rename alert.
    @State private var newName: String = ""
    
    /// State variable holding the `CGRect`s of detected bounding boxes to be drawn.
    /// These are normalized coordinates (0-1, bottom-left origin) from Vision.
    @State private var detectedBoundingBoxes: [CGRect] = []

    // MARK: - Stamp Info State Variables
    
    /// A dictionary to store fetched `StampInfo` for each detected bounding box (`CGRect`).
    /// The `CGRect` key is the normalized bounding box from Vision.
    @State private var fetchedStampData: [CGRect: StampInfo] = [:]
    /// Holds the `StampInfo` for the stamp that was tapped, to be passed to the detail sheet.
    @State private var selectedStampInfoForSheet: StampInfo?
    /// Controls the presentation of the `StampInfoDetailSheet`.
    @State private var showingStampDetailSheet: Bool = false
    
    /// An optional message for displaying errors in an alert.
    @State private var alertMessage: String? = nil
    /// Controls the visibility of error alerts.
    @State private var showingAlert: Bool = false

    // MARK: - Callbacks
    
    /// Callback to `ContentView` to notify that the `ImageModel` has been updated (e.g., name changed, boxes detected).
    /// `ContentView` is responsible for persisting this change.
    var onUpdate: ((ImageModel) -> Void)?
    /// Callback to `ContentView` to notify that this `ImageModel` should be deleted.
    var onDelete: ((ImageModel) -> Void)?

    // MARK: - Services
    
    /// Service responsible for performing image analysis using Vision.
    private let visionService = VisionService()
    /// Service responsible for fetching (currently mock) information about a stamp.
    private let stampInfoService = StampInfoService()

    // MARK: - Body
    
    var body: some View {
        VStack {
            // GeometryReader provides the available size for positioning and scaling the image and overlays.
            GeometryReader { geometry in
                ZStack {
                    // Display the main image.
                    Image(uiImage: imageModel.image)
                        .resizable()
                        .scaledToFit()
                        .overlay(
                            // Overlay for drawing bounding boxes and their market values.
                            ForEach(detectedBoundingBoxes.indices, id: \.self) { index in
                                let boundingBox = detectedBoundingBoxes[index] // Normalized, bottom-left origin
                                let imageSize = imageModel.image.size
                                
                                // Calculate the scaled rectangle for drawing in view coordinates.
                                let (scaledRect, _) = calculateScaledRect(boundingBox: boundingBox, imageSize: imageSize, viewSize: geometry.size)
                                let rectPath = Path(scaledRect)
                                
                                ZStack { // Use ZStack to layer the market value text on top of the stroke.
                                    // Draw the bounding box.
                                    rectPath
                                        .stroke(determineStrokeColor(for: boundingBox), lineWidth: 2)
                                        .contentShape(rectPath) // Make the stroke area tappable.
                                        .onTapGesture {
                                            handleBoundingBoxTap(boundingBox: boundingBox, image: imageModel.image)
                                        }

                                    // Display market value if available.
                                    if let stampInfo = fetchedStampData[boundingBox] {
                                         Text(stampInfo.estimatedMarketValue)
                                             .font(.caption)
                                             .padding(2)
                                             .background(Color.black.opacity(0.7))
                                             .foregroundColor(.white)
                                             .cornerRadius(4)
                                             // Position above the center of the box's top edge.
                                             .position(x: scaledRect.midX, y: scaledRect.minY - 12)
                                     }
                                }
                            }
                        )
                }
                .frame(width: geometry.size.width, height: geometry.size.height)
            }
            .padding()
            // Sheet for displaying detailed stamp information.
            .sheet(isPresented: $showingStampDetailSheet) {
                if let selectedInfo = selectedStampInfoForSheet {
                    StampInfoDetailSheet(stampInfo: selectedInfo)
                }
            }
            // Alert for displaying errors (e.g., from fetching stamp info).
            .alert(isPresented: $showingAlert) {
                Alert(title: Text("Stamp Information"), message: Text(alertMessage ?? "An error occurred."), dismissButton: .default(Text("OK")))
            }

            // Display import timestamp.
            Text("Imported: \(imageModel.timestamp, style: .date) \(imageModel.timestamp, style: .time)")
                .font(.caption)
                .foregroundColor(.gray)
                .padding(.bottom)
            
            // Form for image actions and details.
            Form {
                Section(header: Text("Image Details")) {
                    HStack {
                        Text("Name:")
                        TextField("Image Name", text: $imageModel.name, onCommit: {
                            // When name is committed, call the onUpdate callback.
                            onUpdate?(imageModel)
                        })
                    }
                    // Display status of stamp detection.
                    if !detectedBoundingBoxes.isEmpty {
                        Text("Detected Stamps: \(detectedBoundingBoxes.count)")
                    } else if imageModel.boundingBoxes == nil { // If never processed.
                         Text("Detecting stamps...")
                    } else { // Processed, but none found.
                        Text("No stamps detected previously.")
                    }
                }
                
                Section(header: Text("Actions")) {
                    // Button to trigger renaming the image.
                    Button("Rename Image") {
                        newName = imageModel.name // Pre-fill with current name.
                        showingRenameAlert = true
                    }
                    .alert("Rename Image", isPresented: $showingRenameAlert) {
                        TextField("New Name", text: $newName)
                        Button("OK") {
                            if !newName.isEmpty {
                                var updatedModel = imageModel
                                updatedModel.name = newName
                                onUpdate?(updatedModel) // Notify ContentView.
                                imageModel = updatedModel // Update local state.
                            }
                        }
                        Button("Cancel", role: .cancel) { }
                    } message: {
                        Text("Enter a new name for the image.")
                    }
                    
                    // Button to re-run stamp detection.
                    Button("Re-detect Stamps") {
                        performStampDetection()
                    }

                    // Button to delete the image.
                    Button("Delete Image", role: .destructive) {
                        onDelete?(imageModel) // Notify ContentView.
                        presentationMode.wrappedValue.dismiss() // Dismiss this detail view.
                    }
                }
            }
        }
        .navigationTitle(imageModel.name) // Set navigation bar title to the image name.
        .onAppear {
            newName = imageModel.name // Initialize newName for rename alert.
            // Load existing bounding boxes or perform detection if not already done.
            if let existingBoxes = imageModel.boundingBoxes {
                self.detectedBoundingBoxes = existingBoxes
            } else {
                performStampDetection()
            }
        }
    }
    
    // MARK: - Helper Methods
    
    /// Calculates the display rectangle (in view coordinates) for a given normalized bounding box.
    /// Also returns the scale factor applied to the image.
    /// - Parameters:
    ///   - boundingBox: The normalized `CGRect` (origin bottom-left) from Vision.
    ///   - imageSize: The original size of the `UIImage`.
    ///   - viewSize: The size of the `GeometryReader` containing the image view.
    /// - Returns: A tuple containing the scaled `CGRect` (origin top-left) for display and the scale factor.
    private func calculateScaledRect(boundingBox: CGRect, imageSize: CGSize, viewSize: CGSize) -> (CGRect, CGFloat) {
        let imageAspectRatio = imageSize.width / imageSize.height
        let viewAspectRatio = viewSize.width / viewSize.height
        
        var scale: CGFloat = 1.0
        var offsetX: CGFloat = 0.0
        var offsetY: CGFloat = 0.0

        // Determine how the image is scaled within the view (.scaledToFit)
        if imageAspectRatio > viewAspectRatio { // Image is wider than view (letterboxed)
            scale = viewSize.width / imageSize.width
            offsetY = (viewSize.height - imageSize.height * scale) / 2.0
        } else { // Image is taller than or same aspect ratio as view (pillarboxed)
            scale = viewSize.height / imageSize.height
            offsetX = (viewSize.width - imageSize.width * scale) / 2.0
        }

        // Convert Vision's normalized, bottom-left origin coordinates to SwiftUI's top-left origin, scaled coordinates.
        let scaledRect = CGRect(
            x: (boundingBox.origin.x * imageSize.width * scale) + offsetX,
            y: ((1 - boundingBox.origin.y - boundingBox.height) * imageSize.height * scale) + offsetY,
            width: boundingBox.width * imageSize.width * scale,
            height: boundingBox.height * imageSize.height * scale
        )
        return (scaledRect, scale)
    }

    /// Initiates the stamp detection process using `VisionService`.
    /// Updates the `imageModel` with detected bounding boxes and persists the change via `onUpdate`.
    private func performStampDetection() {
        // Clear previously fetched data and detected boxes before starting a new detection.
        self.fetchedStampData = [:]
        self.detectedBoundingBoxes = []
        
        visionService.detectRectangles(on: imageModel.image) { [self] boxes in
            // Ensure UI updates are on the main thread.
            DispatchQueue.main.async {
                var updatedModel = self.imageModel // Create a mutable copy to update.
                if let boxes = boxes, !boxes.isEmpty {
                    self.detectedBoundingBoxes = boxes
                    updatedModel.boundingBoxes = boxes // Store normalized boxes from Vision.
                } else {
                    // No boxes found or detection failed, ensure local state and model reflect this.
                    self.detectedBoundingBoxes = []
                    updatedModel.boundingBoxes = []
                }
                self.onUpdate?(updatedModel) // Persist changes (including empty boxes if none found).
                self.imageModel = updatedModel // Update local @State.
            }
        }
    }

    /// Handles the tap gesture on a detected bounding box.
    /// This involves cropping the tapped region of the image and fetching stamp information.
    /// - Parameters:
    ///   - boundingBox: The normalized `CGRect` of the tapped bounding box.
    ///   - image: The `UIImage` from which to crop the stamp.
    private func handleBoundingBoxTap(boundingBox: CGRect, image: UIImage) {
        // If data has already been fetched for this specific box, show the sheet directly.
        if let existingInfo = fetchedStampData[boundingBox] {
            self.selectedStampInfoForSheet = existingInfo
            self.showingStampDetailSheet = true
            return
        }

        // 1. Crop Image: Convert normalized Vision coordinates to pixel coordinates for cropping.
        let imageWidth = image.size.width
        let imageHeight = image.size.height
        
        let cropRectPx = CGRect(
            x: boundingBox.origin.x * imageWidth,
            y: (1 - boundingBox.origin.y - boundingBox.height) * imageHeight, // Convert Y-origin
            width: boundingBox.width * imageWidth,
            height: boundingBox.height * imageHeight
        )

        guard let cgImage = image.cgImage,
              let croppedCGImage = cgImage.cropping(to: cropRectPx) else {
            print("Error: Failed to crop image for bounding box \(boundingBox). Using full image as fallback.")
            // Fallback: fetch info using the full image if cropping fails.
            // Consider alerting the user that cropping failed.
            fetchInfo(for: image, originalBoundingBox: boundingBox)
            return
        }
        let croppedImage = UIImage(cgImage: croppedCGImage)
        
        // 2. Fetch Info: Use the cropped image.
        fetchInfo(for: croppedImage, originalBoundingBox: boundingBox)
    }

    /// Fetches stamp information for a given image (typically a cropped stamp) and updates the view's state.
    /// - Parameters:
    ///   - imageToFetch: The `UIImage` for which to fetch information.
    ///   - originalBoundingBox: The original normalized `CGRect` key used to store results in `fetchedStampData`.
    private func fetchInfo(for imageToFetch: UIImage, originalBoundingBox: CGRect) {
        print("Fetching info for box: \(originalBoundingBox)...")
        // Placeholder for loading indicator for this specific box could be added here.

        stampInfoService.fetchStampInfo(for: imageToFetch) { result in
            DispatchQueue.main.async {
                switch result {
                case .success(let stampInfo):
                    self.fetchedStampData[originalBoundingBox] = stampInfo
                    self.selectedStampInfoForSheet = stampInfo
                    self.showingStampDetailSheet = true
                case .failure(let error):
                    print("Error fetching stamp info for box \(originalBoundingBox): \(error.localizedDescription)")
                    // Store nil to indicate fetch failure for this box (impacts color coding).
                    self.fetchedStampData[originalBoundingBox] = nil 
                    self.alertMessage = "Failed to fetch stamp details: \(error.localizedDescription)"
                    self.showingAlert = true
                }
            }
        }
    }

    /// Determines the stroke color for a bounding box based on its fetched `StampInfo`.
    /// - Parameter boundingBox: The normalized `CGRect` of the bounding box.
    /// - Returns: A `Color` for the stroke.
    private func determineStrokeColor(for boundingBox: CGRect) -> Color {
        guard let stampInfo = fetchedStampData[boundingBox] else {
            // If no StampInfo (fetch not attempted or failed), color it grey.
            return .gray 
        }

        // Parse estimated market value (simplified for mock data).
        let valueString = stampInfo.estimatedMarketValue.lowercased()
        let numbers = valueString.components(separatedBy: CharacterSet(charactersIn: "0123456789.").inverted)
            .compactMap { Double($0) }
            .filter { $0 > 0 }
        
        let highestValue = numbers.max() ?? 0.0

        if highestValue > 20.0 {
            return .yellow // Higher value stamps.
        } else {
            return Color.blue.opacity(0.8) // Lower value or default.
        }
    }
}

// MARK: - Preview

struct ImageDetailView_Previews: PreviewProvider {
    static var previews: some View {
        // Create a dummy UIImage for the preview.
        let previewImage = UIImage(systemName: "photo.on.rectangle.angled") ?? UIImage()
        // Create a sample ImageModel.
        let dummyImageModel = ImageModel(
            name: "Preview Stamp Image",
            image: previewImage,
            timestamp: Date(),
            // Example with a pre-defined bounding box for preview visualization.
            boundingBoxes: [CGRect(x: 0.25, y: 0.25, width: 0.5, height: 0.5)] 
        )
        
        NavigationView {
            ImageDetailView(imageModel: dummyImageModel, onUpdate: { model in
                print("Preview: ImageModel updated - \(model.name)")
            }, onDelete: { model in
                print("Preview: ImageModel deleted - \(model.name)")
            })
        }
    }
}
