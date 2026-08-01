import Testing
@testable import FitCrewHealthCore

@Test func glucoseConvertsMmolPerLitreToMgPerDecilitre() throws {
    let normalized = try HealthUnitNormalizer.normalize(
        kind: .bloodGlucose,
        value: 5.6,
        unit: "mmol/L"
    )

    #expect(abs(normalized.value - 100.90192) < 0.00001)
    #expect(normalized.unit == "mg/dL")
}

@Test func requestedTypesRemainOnTheApprovedMinimumList() {
    #expect(HealthDataKind.allCases == [
        .bloodGlucose,
        .sleepAsleep,
        .sleepCore,
        .sleepDeep,
        .sleepREM,
        .heartRateVariability,
        .restingHeartRate,
        .workout,
        .activeEnergy,
        .stepCount,
        .standHours,
        .activitySummary,
    ])
}
