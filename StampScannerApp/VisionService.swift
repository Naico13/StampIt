import Vision
import UIKit

class VisionService {
    func detectRectangles(on image: UIImage, completion: @escaping ([CGRect]?) -> Void) {
        guard let cgImage = image.cgImage else {
            completion(nil)
            return
        }

        let requestHandler = VNImageRequestHandler(cgImage: cgImage, options: [:])
        let request = VNDetectRectanglesRequest { (request, error) in
            if let error = error {
                print("Error detecting rectangles: \(error)")
                completion(nil)
                return
            }

            guard let observations = request.results as? [VNRectangleObservation] else {
                completion(nil)
                return
            }

            let boundingBoxes = observations.map { observation -> CGRect in
                // VNRectangleObservation's boundingBox is normalized to image dimensions (0-1)
                // with origin at bottom-left. SwiftUI's coordinate system is top-left.
                // We need to convert these coordinates.
                let boundingBox = observation.boundingBox
                // For now, let's return the normalized CGRect.
                // Conversion to view coordinates will be handled in the View.
                return boundingBox
            }
            completion(boundingBoxes)
        }

        // Configure the request (optional, but good for tuning)
        // request.minimumAspectRatio = 0.2 // Example: Minimum aspect ratio of detected rectangles
        // request.maximumAspectRatio = 1.0 // Example: Maximum aspect ratio
        // request.minimumSize = 0.1       // Example: Minimum size relative to image dimension
        // request.maximumObservations = 0 // No limit on observations

        DispatchQueue.global(qos: .userInitiated).async {
            do {
                try requestHandler.perform([request])
                // The completion handler (passed from ImageDetailView) is already responsible
                // for dispatching UI updates to the main thread. So, no DispatchQueue.main.async needed here for `completion(boundingBoxes)`.
            } catch {
                print("Failed to perform Vision request: \(error)")
                // Ensure completion is called, even on error.
                // ImageDetailView's completion handler will handle UI updates on the main thread.
                completion(nil)
            }
        }
    }
}
