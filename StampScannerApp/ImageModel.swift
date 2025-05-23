//
//  ImageModel.swift
//  StampScannerApp
//
//  Created by [Your Name]
//  Copyright © [Year] [Your Organization]. All rights reserved.
//
//  This file defines the data model for an imported image, including its metadata,
//  storage path, and methods for persistence and thumbnail generation.
//

import SwiftUI
import Vision // For CGRect, although it's CoreGraphics.CGRect

/// Represents an image imported by the user, along with its metadata and detected stamp bounding boxes.
/// Conforms to `Identifiable` for use in SwiftUI lists and `Codable` for persistence.
struct ImageModel: Identifiable, Codable {
    /// A unique identifier for the image model.
    let id: UUID
    /// The user-defined name for the image.
    var name: String
    /// The file path where the original imported image is stored in the app's documents directory.
    let imagePath: String
    /// The timestamp when the image was imported.
    let timestamp: Date
    /// An array of `CGRect` values representing the normalized bounding boxes of detected stamps.
    /// These coordinates are relative to the image's dimensions, with the origin at the bottom-left.
    var boundingBoxes: [CGRect]?

    // Custom coding keys to handle the encoding/decoding of `boundingBoxes` (CGRect is not directly Codable).
    enum CodingKeys: String, CodingKey {
        case id, name, imagePath, timestamp
        case boundingBoxesData // Use a different key for the Data representation of boundingBoxes
    }

    /// Initializes a new `ImageModel`.
    ///
    /// When an `ImageModel` is created, the provided `UIImage` is saved as a JPEG
    /// to a unique path in the app's documents directory.
    ///
    /// - Parameters:
    ///   - id: A unique UUID for the model. Defaults to a new UUID.
    ///   - name: The name for the image.
    ///   - image: The `UIImage` to be stored.
    ///   - timestamp: The import timestamp. Defaults to the current date and time.
    ///   - boundingBoxes: Optional array of `CGRect` for detected stamps. Defaults to `nil`.
    init(id: UUID = UUID(), name: String, image: UIImage, timestamp: Date = Date(), boundingBoxes: [CGRect]? = nil) {
        self.id = id
        self.name = name
        self.timestamp = timestamp
        self.boundingBoxes = boundingBoxes

        // Create a unique path for the image in the documents directory.
        let documentsDirectory = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        self.imagePath = documentsDirectory.appendingPathComponent("\(id.uuidString).jpg").path

        // Save the image data to the path.
        if let data = image.jpegData(compressionQuality: 0.8) {
            do {
                try data.write(to: URL(fileURLWithPath: imagePath))
            } catch {
                // In a production app, this error should be propagated or logged more robustly.
                print("Error saving image \(id.uuidString): \(error)")
            }
        }
    }

    /// A computed property that loads the `UIImage` from the stored `imagePath`.
    ///
    /// - Returns: The `UIImage` loaded from disk, or a default empty `UIImage` if loading fails.
    var image: UIImage {
        UIImage(contentsOfFile: imagePath) ?? UIImage() // Return a default empty image if loading fails
    }

    // MARK: - Codable Conformance

    /// Initializes an `ImageModel` instance from a decoder.
    /// Required for `Codable` conformance, handles custom decoding of `boundingBoxes`.
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(UUID.self, forKey: .id)
        name = try container.decode(String.self, forKey: .name)
        imagePath = try container.decode(String.self, forKey: .imagePath)
        timestamp = try container.decode(Date.self, forKey: .timestamp)
        
        // Decode boundingBoxesData as Data, then unarchive to [CGRect]
        if let data = try container.decodeIfPresent(Data.self, forKey: .boundingBoxesData) {
            do {
                // Note: Using NSKeyedUnarchiver for CGRect array. Ensure secure coding if possible,
                // or consider a more modern approach if complex objects were involved.
                // For CGRect, this is generally acceptable for simplicity.
                if let unarchivedBoxes = try NSKeyedUnarchiver.unarchivedObject(ofClass: NSArray.self, from: data) as? [CGRect] {
                    boundingBoxes = unarchivedBoxes
                } else {
                    // This case means data was present but not in the expected [CGRect] format.
                    // Depending on strictness, could throw an error or default to nil.
                    print("Warning: Could not unarchive boundingBoxes for \(id.uuidString) as [CGRect].")
                    boundingBoxes = nil
                }
            } catch {
                print("Error unarchiving boundingBoxes for \(id.uuidString): \(error). Setting to nil.")
                boundingBoxes = nil // Or rethrow a custom decoding error
            }
        } else {
            boundingBoxes = nil
        }
    }

    /// Encodes this `ImageModel` instance into an encoder.
    /// Required for `Codable` conformance, handles custom encoding of `boundingBoxes`.
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(id, forKey: .id)
        try container.encode(name, forKey: .name)
        try container.encode(imagePath, forKey: .imagePath)
        try container.encode(timestamp, forKey: .timestamp)
        
        // Archive boundingBoxes to Data, then encode if present
        if let boundingBoxes = boundingBoxes, !boundingBoxes.isEmpty {
            do {
                let data = try NSKeyedArchiver.archivedData(withRootObject: boundingBoxes, requiringSecureCoding: false)
                try container.encode(data, forKey: .boundingBoxesData)
            } catch {
                // In a production app, this error should be handled more gracefully.
                print("Error archiving boundingBoxes for \(id.uuidString): \(error)")
            }
        }
    }

    /// Generates a thumbnail `UIImage` for the image.
    ///
    /// This method resizes the full image to the specified target size. For performance in a
    /// production app, consider caching thumbnails on disk or using a more advanced
    /// image processing library if very high-quality thumbnails are needed.
    ///
    /// - Parameter size: The target size for the thumbnail. Defaults to 100x100 points.
    /// - Returns: A `UIImage` instance representing the thumbnail, or `nil` if thumbnail generation fails.
    ///            Returns the original image if it's already smaller than the target size or if it's an empty placeholder.
    func thumbnail(size: CGSize = CGSize(width: 100, height: 100)) -> UIImage? {
        let fullImage = self.image // Accesses the computed property that loads from disk
        
        // Check if the fullImage is already small enough or is an empty placeholder (size 0x0)
        guard fullImage.size.width > 0, fullImage.size.height > 0 else {
            return fullImage // Return the empty/placeholder image as is
        }
        
        guard (fullImage.size.width > size.width || fullImage.size.height > size.height) else {
            return fullImage // Return original if it's already smaller than or equal to target size
        }

        let renderer = UIGraphicsImageRenderer(size: size)
        return renderer.image { (context) in
            fullImage.draw(in: CGRect(origin: .zero, size: size))
        }
    }
}

/// Custom error types that can occur during `ImageModel` operations, particularly persistence.
enum ImageModelError: Error {
    /// Error during saving of the `ImageModel` array (e.g., to JSON).
    case fileSaveError(Error)
    /// Error during loading of the `ImageModel` array.
    case fileLoadError(Error)
    /// Error during JSON encoding.
    case encodingError(Error)
    /// Error during JSON decoding.
    case decodingError(Error)
    /// Failure to access the documents directory.
    case directoryUnavailable
    /// Error saving an individual image file (e.g., the JPEG).
    case imageSaveError(Error)
}


/// Extension on an array of `ImageModel` to provide static methods for loading and saving
/// the entire array to/from disk.
extension [ImageModel] {
    /// Loads an array of `ImageModel` instances from a JSON file ("images.json") in the app's documents directory.
    ///
    /// - Returns: A `Result` containing an array of `ImageModel` on success, or an `ImageModelError` on failure.
    ///            Returns an empty array in `Result.success` if the file does not exist (considered a non-error state for initial launch).
    static func loadFromFile() -> Result<[ImageModel], ImageModelError> {
        guard let documentsDirectory = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first else {
            return .failure(.directoryUnavailable)
        }
        let archiveURL = documentsDirectory.appendingPathComponent("images.json")
        
        do {
            let data = try Data(contentsOf: archiveURL)
            let decoder = JSONDecoder()
            let models = try decoder.decode([ImageModel].self, from: data)
            return .success(models)
        } catch let error as NSError where error.domain == NSCocoaErrorDomain && error.code == NSFileReadNoSuchFileError {
            // If the file doesn't exist, it's not an error for loading; just means no data saved yet.
            return .success([])
        } catch {
            if let decodingError = error as? DecodingError {
                 return .failure(.decodingError(decodingError))
            }
            return .failure(.fileLoadError(error))
        }
    }

    /// Saves the array of `ImageModel` instances to a JSON file ("images.json") in the app's documents directory.
    ///
    /// - Returns: A `Result` indicating success (`Void`) or an `ImageModelError` on failure.
    func saveToFile() -> Result<Void, ImageModelError> {
        guard let documentsDirectory = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first else {
            return .failure(.directoryUnavailable)
        }
        let archiveURL = documentsDirectory.appendingPathComponent("images.json")
        
        let encoder = JSONDecoder()
        do {
            let encoded = try encoder.encode(self)
            // Using .atomicWrite ensures that the file is only replaced if the write is successful,
            // reducing risk of data corruption if the app crashes during save.
            try encoded.write(to: archiveURL, options: [.atomicWrite])
            return .success(())
        } catch let error as EncodingError {
            return .failure(.encodingError(error))
        } catch {
            return .failure(.fileSaveError(error))
        }
    }
}
