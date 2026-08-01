import CryptoKit
import Foundation

public enum BatchBuilder {
    public static func stableBatchID(
        deviceBindingID: String,
        cursor: String,
        sampleIDs: [String]
    ) -> UUID {
        let canonical = ([deviceBindingID, cursor] + sampleIDs.sorted()).joined(separator: "\n")
        let digest = SHA256.hash(data: Data(canonical.utf8))
        var hex = digest.prefix(16).map { String(format: "%02x", $0) }.joined()
        let versionIndex = hex.index(hex.startIndex, offsetBy: 12)
        hex.replaceSubrange(versionIndex...versionIndex, with: "4")
        let variantIndex = hex.index(hex.startIndex, offsetBy: 16)
        let variant = Int(String(hex[variantIndex]), radix: 16) ?? 0
        let variantCharacter = String(format: "%x", (variant & 0x3) | 0x8)
        hex.replaceSubrange(variantIndex...variantIndex, with: variantCharacter)
        let first = String(hex.prefix(8))
        let second = String(hex.dropFirst(8).prefix(4))
        let third = String(hex.dropFirst(12).prefix(4))
        let fourth = String(hex.dropFirst(16).prefix(4))
        let fifth = String(hex.dropFirst(20).prefix(12))
        let formatted = "\(first)-\(second)-\(third)-\(fourth)-\(fifth)"
        return UUID(uuidString: formatted)!
    }
}
