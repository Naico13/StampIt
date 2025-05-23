import SwiftUI

struct StampInfoDetailSheet: View {
    @Environment(\.presentationMode) var presentationMode
    let stampInfo: StampInfo

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 15) {
                    Group {
                        Text("Stamp Details").font(.largeTitle).padding(.bottom)
                        
                        InfoRow(label: "Name", value: stampInfo.name)
                        InfoRow(label: "Country", value: stampInfo.country)
                        InfoRow(label: "Date of Issuance", value: stampInfo.dateOfIssuance)
                        InfoRow(label: "Rarity", value: stampInfo.rarity)
                        InfoRow(label: "Face Value", value: stampInfo.faceValue)
                        InfoRow(label: "Estimated Market Value", value: stampInfo.estimatedMarketValue)
                    }
                    
                    Text("History")
                        .font(.title2)
                        .padding(.top)
                    Text(stampInfo.history)
                        .font(.body)
                    
                    Text("Sources")
                        .font(.title2)
                        .padding(.top)
                    if stampInfo.sourceURLs.isEmpty {
                        Text("No sources listed.")
                            .font(.body)
                            .foregroundColor(.gray)
                    } else {
                        ForEach(stampInfo.sourceURLs, id: \.self) { urlString in
                            if let url = URL(string: urlString) {
                                Link(urlString, destination: url)
                                    .font(.body)
                            } else {
                                Text("Invalid URL: \(urlString)")
                                    .font(.body)
                                    .foregroundColor(.red)
                            }
                        }
                    }
                }
                .padding()
            }
            .navigationTitle("Stamp Information")
            .navigationBarItems(trailing: Button("Dismiss") {
                presentationMode.wrappedValue.dismiss()
            })
        }
    }
}

struct InfoRow: View {
    let label: String
    let value: String

    var body: some View {
        VStack(alignment: .leading) {
            Text(label)
                .font(.headline)
            Text(value)
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
    }
}

struct StampInfoDetailSheet_Previews: PreviewProvider {
    static var previews: some View {
        StampInfoDetailSheet(stampInfo: StampInfo.mockData())
    }
}
