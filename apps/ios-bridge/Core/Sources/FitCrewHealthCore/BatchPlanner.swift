import Foundation

public enum BatchPlanningError: Error, Equatable {
    case missingConsent(HealthDataKind)
}

public enum BatchPlanner {
    public static func makeBatches(
        deviceBindingID: UUID,
        consentIDs: [String: UUID],
        cursor: String,
        source: String,
        timezone: String,
        sentAt: Date,
        fullReconciliation: Bool,
        samples: [HealthSampleDTO]
    ) throws -> [HealthSyncBatchDTO] {
        let grouped = Dictionary(grouping: samples, by: \.kind)
        return try grouped.keys.sorted { $0.rawValue < $1.rawValue }.map { kind in
            guard let consentID = consentIDs[kind.rawValue] else {
                throw BatchPlanningError.missingConsent(kind)
            }
            let categorySamples = grouped[kind] ?? []
            let batchID = BatchBuilder.stableBatchID(
                deviceBindingID: deviceBindingID.uuidString,
                cursor: "\(cursor):\(kind.rawValue)",
                sampleIDs: categorySamples.map { $0.sampleID.uuidString }
            )
            return HealthSyncBatchDTO(
                batchID: batchID,
                deviceBindingID: deviceBindingID,
                consentID: consentID,
                source: source,
                timezone: timezone,
                sentAt: sentAt,
                fullReconciliation: fullReconciliation,
                samples: categorySamples
            )
        }
    }
}
