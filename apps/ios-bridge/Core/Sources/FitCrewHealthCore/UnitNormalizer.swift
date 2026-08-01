public struct NormalizedValue: Equatable, Sendable {
    public let value: Double
    public let unit: String
}

public enum HealthUnitError: Error, Equatable {
    case unsupportedGlucoseUnit(String)
}

public enum HealthUnitNormalizer {
    public static func normalize(
        kind: HealthDataKind,
        value: Double,
        unit: String
    ) throws -> NormalizedValue {
        guard kind == .bloodGlucose else {
            return NormalizedValue(value: value, unit: unit)
        }
        switch unit.lowercased().replacingOccurrences(of: " ", with: "") {
        case "mmol/l":
            return NormalizedValue(value: value * 18.0182, unit: "mg/dL")
        case "mg/dl":
            return NormalizedValue(value: value, unit: "mg/dL")
        default:
            throw HealthUnitError.unsupportedGlucoseUnit(unit)
        }
    }
}
