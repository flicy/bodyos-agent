import Foundation
import Testing
@testable import FitCrewHealthCore

@Test func stableBatchIDIsIndependentOfSampleOrder() throws {
    let first = BatchBuilder.stableBatchID(
        deviceBindingID: "device-1",
        cursor: "cursor-1",
        sampleIDs: ["b", "a"]
    )
    let second = BatchBuilder.stableBatchID(
        deviceBindingID: "device-1",
        cursor: "cursor-1",
        sampleIDs: ["a", "b"]
    )

    #expect(first == second)
}

@Test func encodedBatchMatchesVersionedContractKeys() throws {
    let instant = Date(timeIntervalSince1970: 1_785_556_800)
    let sample = HealthSampleDTO(
        sampleID: UUID(uuidString: "55555555-5555-4555-8555-555555555555")!,
        kind: .bloodGlucose,
        startAt: instant,
        endAt: instant,
        value: 5.6,
        unit: "mmol/L",
        source: "com.yuwell.anytime",
        device: nil
    )
    let batch = HealthSyncBatchDTO(
        batchID: UUID(uuidString: "44444444-4444-4444-8444-444444444444")!,
        deviceBindingID: UUID(uuidString: "22222222-2222-4222-8222-222222222222")!,
        consentID: UUID(uuidString: "33333333-3333-4333-8333-333333333333")!,
        source: "com.yuwell.anytime",
        timezone: "Asia/Shanghai",
        sentAt: instant,
        fullReconciliation: false,
        samples: [sample]
    )

    let data = try JSONEncoder.fitCrew.encode(batch)
    let json = try #require(JSONSerialization.jsonObject(with: data) as? [String: Any])

    #expect(json["schema_version"] as? String == "health-sync.v1")
    #expect(json["device_binding_id"] != nil)
    #expect(json["feishu_open_id"] == nil)
}

@Test func plannerCreatesOneConsentBoundBatchPerHealthCategory() throws {
    let deviceID = UUID(uuidString: "22222222-2222-4222-8222-222222222222")!
    let glucoseConsent = UUID(uuidString: "33333333-3333-4333-8333-333333333333")!
    let workoutConsent = UUID(uuidString: "66666666-6666-4666-8666-666666666666")!
    let samples = [
        HealthSampleDTO(
            sampleID: UUID(uuidString: "55555555-5555-4555-8555-555555555555")!,
            kind: .bloodGlucose,
            startAt: Date(timeIntervalSince1970: 0),
            endAt: Date(timeIntervalSince1970: 0),
            value: 100,
            unit: "mg/dL",
            source: "yuwell",
            device: nil
        ),
        HealthSampleDTO(
            sampleID: UUID(uuidString: "77777777-7777-4777-8777-777777777777")!,
            kind: .workout,
            startAt: Date(timeIntervalSince1970: 0),
            endAt: Date(timeIntervalSince1970: 60),
            value: 60,
            unit: "s",
            source: "apple",
            device: nil
        ),
    ]

    let batches = try BatchPlanner.makeBatches(
        deviceBindingID: deviceID,
        consentIDs: [
            HealthDataKind.bloodGlucose.rawValue: glucoseConsent,
            HealthDataKind.workout.rawValue: workoutConsent,
        ],
        cursor: "cursor-1",
        source: "apple-healthkit",
        timezone: "Asia/Shanghai",
        sentAt: Date(timeIntervalSince1970: 120),
        fullReconciliation: false,
        samples: samples
    )

    #expect(batches.count == 2)
    #expect(batches.allSatisfy { Set($0.samples.map(\.kind)).count == 1 })
    #expect(Set(batches.map(\.consentID)) == Set([glucoseConsent, workoutConsent]))
}

@Test func plannerFailsClosedWhenAConsentIsMissing() {
    let sample = HealthSampleDTO(
        sampleID: UUID(),
        kind: .bloodGlucose,
        startAt: Date(timeIntervalSince1970: 0),
        endAt: Date(timeIntervalSince1970: 0),
        value: 100,
        unit: "mg/dL",
        source: "yuwell",
        device: nil
    )

    #expect(throws: BatchPlanningError.missingConsent(.bloodGlucose)) {
        try BatchPlanner.makeBatches(
            deviceBindingID: UUID(),
            consentIDs: [:],
            cursor: "cursor-1",
            source: "apple-healthkit",
            timezone: "Asia/Shanghai",
            sentAt: Date(),
            fullReconciliation: false,
            samples: [sample]
        )
    }
}
