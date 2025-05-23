import SwiftUI

struct ContentView: View {
    @State private var showingImagePicker = false
    @State private var inputImage: UIImage?
    // Initialize images as empty, load them in onAppear
    @State private var images: [ImageModel] = []
    @State private var showingFileErrorAlert = false
    @State private var fileErrorMessage = ""

    var body: some View {
        NavigationView {
            VStack {
                if images.isEmpty {
                    Text("No images imported yet.")
                        .foregroundColor(.gray)
                } else {
                    List {
                        ForEach(images) { imageModel in
                            NavigationLink(destination: ImageDetailView(
                                imageModel: imageModel,
                                onUpdate: { updatedImageModel in
                                    if let index = images.firstIndex(where: { $0.id == updatedImageModel.id }) {
                                        images[index] = updatedImageModel
                                        saveImagesToDisk()
                                    }
                                },
                                onDelete: { imageModelToDelete in
                                    deleteImage(imageModelToDelete)
                                }
                            )) {
                                HStack {
                                    // Use the thumbnail method
                                    Image(uiImage: imageModel.thumbnail(size: CGSize(width: 50, height: 50)) ?? UIImage(systemName: "photo.fill")!)
                                        .resizable()
                                        .scaledToFit() // or .scaledToFill().clipped() depending on desired look
                                        .frame(width: 50, height: 50)
                                        .cornerRadius(4) // Optional: for softer edges
                                    Text(imageModel.name)
                                }
                            }
                        }
                        .onDelete(perform: deleteImagesAtIndexSet)
                    }
                }

                Spacer()

                Button("Import Image") {
                    showingImagePicker = true
                }
                .padding()
                .sheet(isPresented: $showingImagePicker, onDismiss: loadImage) {
                    ImagePicker(image: $inputImage)
                }
            }
            .navigationTitle("Stamp Scanner")
            .onAppear {
                loadImagesFromDisk()
            }
            .alert(isPresented: $showingFileErrorAlert) {
                Alert(title: Text("File Operation Error"), message: Text(fileErrorMessage), dismissButton: .default(Text("OK")))
            }
        }
    }

    func loadImagesFromDisk() {
        let result = [ImageModel].loadFromFile()
        switch result {
        case .success(let loadedImages):
            self.images = loadedImages
        case .failure(let error):
            self.fileErrorMessage = "Failed to load images: \(error.localizedDescription)"
            self.showingFileErrorAlert = true
            // Optionally, set images to empty or handle differently
            self.images = [] 
        }
    }
    
    func saveImagesToDisk() {
        let result = images.saveToFile()
        if case .failure(let error) = result {
            self.fileErrorMessage = "Failed to save images: \(error.localizedDescription)"
            self.showingFileErrorAlert = true
        }
    }

    func loadImage() {
        guard let inputImage = inputImage else { return }
        let imageName = "Stamp Image \(String(format: "%.0f", Date().timeIntervalSince1970))"
        
        // ImageModel init now also needs to handle potential errors if we make it throwing for image saving
        // For now, assuming ImageModel init itself doesn't throw ImageModelError directly,
        // but it would be the next step for full error propagation.
        let newImageModel = ImageModel(name: imageName, image: inputImage, timestamp: Date())
        images.append(newImageModel)
        saveImagesToDisk()
        self.inputImage = nil
    }

    func deleteImagesAtIndexSet(at offsets: IndexSet) {
        let imagesToDelete = offsets.map { images[$0] }
        for imageModel in imagesToDelete {
            deleteImageFromFileSystem(imageModel: imageModel) // This one still uses try?
        }
        images.remove(atOffsets: offsets)
        saveImagesToDisk()
    }
    
    func deleteImage(_ imageModel: ImageModel) {
        deleteImageFromFileSystem(imageModel: imageModel) // This one still uses try?
        images.removeAll { $0.id == imageModel.id }
        saveImagesToDisk()
    }

    private func deleteImageFromFileSystem(imageModel: ImageModel) {
        // This function should also be updated to return Result or throw
        // for complete error handling. For now, it's left as is from previous version.
        let fileManager = FileManager.default
        do {
            try fileManager.removeItem(atPath: imageModel.imagePath)
        } catch {
            print("Error deleting image file: \(error)")
            // Ideally, this error should also be surfaced to the user.
            // self.fileErrorMessage = "Failed to delete image file '\(imageModel.name)': \(error.localizedDescription)"
            // self.showingFileErrorAlert = true
        }
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
