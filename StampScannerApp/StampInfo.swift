import Foundation

struct StampInfo: Codable, Identifiable {
    let id: UUID
    var name: String
    var country: String
    var dateOfIssuance: String
    var rarity: String
    var faceValue: String
    var estimatedMarketValue: String
    var history: String
    var sourceURLs: [String]

    // Default initializer
    init(id: UUID = UUID(),
         name: String,
         country: String,
         dateOfIssuance: String,
         rarity: String,
         faceValue: String,
         estimatedMarketValue: String,
         history: String,
         sourceURLs: [String]) {
        self.id = id
        self.name = name
        self.country = country
        self.dateOfIssuance = dateOfIssuance
        self.rarity = rarity
        self.faceValue = faceValue
        self.estimatedMarketValue = estimatedMarketValue
        self.history = history
        self.sourceURLs = sourceURLs
    }
}

// Example Mock Data Generator (can be moved or expanded)
extension StampInfo {
    static func mockData() -> StampInfo {
        return StampInfo(
            name: "Mock Penny Black",
            country: "Mock Great Britain",
            dateOfIssuance: "May 1, 1840",
            rarity: "Common (Mock)",
            faceValue: "One Penny (Mock)",
            estimatedMarketValue: "$5 - $50 (Mock)",
            history: "This is a mock history of the first adhesive postage stamp used in a public postal system. It was issued in Great Britain on 1 May 1840. (Mock Data)",
            sourceURLs: ["https://mock.wikipedia.org/wiki/Penny_Black", "https://mock.example-stamp-collectors.com/penny-black"]
        )
    }
    
    static func anotherMockData() -> StampInfo {
         return StampInfo(
             name: "Mock Inverted Jenny",
             country: "Mock USA",
             dateOfIssuance: "May 10, 1918",
             rarity: "Extremely Rare (Mock)",
             faceValue: "24 Cents (Mock)",
             estimatedMarketValue: "$1,000,000 - $2,000,000 (Mock)",
             history: "A famous mock US postage stamp with an error: the image of the Curtiss JN-4 airplane in the center is printed upside-down. (Mock Data)",
             sourceURLs: ["https://mock.wikipedia.org/wiki/Inverted_Jenny", "https://mock.example-stamp-collectors.com/inverted-jenny"]
         )
     }
}
