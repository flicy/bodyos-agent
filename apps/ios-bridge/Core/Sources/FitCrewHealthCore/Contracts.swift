import Foundation

public enum HealthDataKind: String, Codable, CaseIterable, Hashable, Sendable {
    case bloodGlucose = "blood_glucose"
    case sleepAsleep = "sleep_asleep"
    case sleepCore = "sleep_core"
    case sleepDeep = "sleep_deep"
    case sleepREM = "sleep_rem"
    case heartRateVariability = "heart_rate_variability"
    case restingHeartRate = "resting_heart_rate"
    case workout
    case activeEnergy = "active_energy"
    case stepCount = "step_count"
    case standHours = "stand_hours"
    case activitySummary = "activity_summary"
}

public struct HealthSampleDTO: Codable, Equatable, Sendable {
    public let sampleID: UUID
    public let kind: HealthDataKind
    public let startAt: Date
    public let endAt: Date
    public let value: Double
    public let unit: String
    public let source: String
    public let device: String?

    public init(
        sampleID: UUID,
        kind: HealthDataKind,
        startAt: Date,
        endAt: Date,
        value: Double,
        unit: String,
        source: String,
        device: String?
    ) {
        self.sampleID = sampleID
        self.kind = kind
        self.startAt = startAt
        self.endAt = endAt
        self.value = value
        self.unit = unit
        self.source = source
        self.device = device
    }

    enum CodingKeys: String, CodingKey {
        case sampleID = "sample_id"
        case kind
        case startAt = "start_at"
        case endAt = "end_at"
        case value
        case unit
        case source
        case device
    }
}

public struct HealthSyncBatchDTO: Codable, Equatable, Sendable {
    public let schemaVersion = "health-sync.v1"
    public let batchID: UUID
    public let deviceBindingID: UUID
    public let consentID: UUID
    public let source: String
    public let timezone: String
    public let sentAt: Date
    public let fullReconciliation: Bool
    public let samples: [HealthSampleDTO]

    public init(
        batchID: UUID,
        deviceBindingID: UUID,
        consentID: UUID,
        source: String,
        timezone: String,
        sentAt: Date,
        fullReconciliation: Bool,
        samples: [HealthSampleDTO]
    ) {
        self.batchID = batchID
        self.deviceBindingID = deviceBindingID
        self.consentID = consentID
        self.source = source
        self.timezone = timezone
        self.sentAt = sentAt
        self.fullReconciliation = fullReconciliation
        self.samples = samples
    }

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case batchID = "batch_id"
        case deviceBindingID = "device_binding_id"
        case consentID = "consent_id"
        case source
        case timezone
        case sentAt = "sent_at"
        case fullReconciliation = "full_reconciliation"
        case samples
    }
}

public extension JSONEncoder {
    static var fitCrew: JSONEncoder {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.sortedKeys]
        return encoder
    }
}
