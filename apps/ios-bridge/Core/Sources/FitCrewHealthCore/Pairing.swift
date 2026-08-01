import Foundation

public struct PairingPayload: Codable, Equatable, Sendable {
    public let baseURL: URL
    public let deviceBindingID: UUID
    public let consentIDs: [String: UUID]
    public let deviceToken: String
}

public enum PairingError: Error, Equatable {
    case invalidURL
    case invalidPayload
}

public enum PairingDecoder {
    public static func decode(_ url: URL) throws -> PairingPayload {
        guard url.scheme == "fitcrew-health", url.host == "configure",
              let components = URLComponents(url: url, resolvingAgainstBaseURL: false),
              let encoded = components.queryItems?.first(where: { $0.name == "payload" })?.value
        else {
            throw PairingError.invalidURL
        }
        let normalized = encoded
            .replacingOccurrences(of: "-", with: "+")
            .replacingOccurrences(of: "_", with: "/")
        let padded = normalized + String(repeating: "=", count: (4 - normalized.count % 4) % 4)
        guard let data = Data(base64Encoded: padded),
              let payload = try? JSONDecoder().decode(PairingPayload.self, from: data),
              payload.baseURL.scheme == "https",
              !payload.deviceToken.isEmpty,
              !payload.consentIDs.isEmpty
        else {
            throw PairingError.invalidPayload
        }
        return payload
    }
}
