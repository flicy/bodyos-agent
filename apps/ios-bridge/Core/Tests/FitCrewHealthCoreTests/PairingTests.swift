import Foundation
import Testing
@testable import FitCrewHealthCore

@Test func pairingURLDecodesProvisioningSecretsLocally() throws {
    let json = """
    {"baseURL":"https://bodyos.example.test","consentIDs":{"blood_glucose":"33333333-3333-4333-8333-333333333333"},"deviceBindingID":"22222222-2222-4222-8222-222222222222","deviceToken":"one-time-token"}
    """
    let encoded = Data(json.utf8).base64EncodedString()
        .replacingOccurrences(of: "+", with: "-")
        .replacingOccurrences(of: "/", with: "_")
        .replacingOccurrences(of: "=", with: "")
    let url = URL(string: "fitcrew-health://configure?payload=\(encoded)")!

    let pairing = try PairingDecoder.decode(url)

    #expect(pairing.baseURL.absoluteString == "https://bodyos.example.test")
    #expect(pairing.deviceToken == "one-time-token")
    #expect(pairing.consentIDs["blood_glucose"] != nil)
}

@Test func pairingRejectsUnexpectedSchemes() {
    #expect(throws: PairingError.invalidURL) {
        try PairingDecoder.decode(URL(string: "https://example.test/configure?payload=nope")!)
    }
}
