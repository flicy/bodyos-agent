import FitCrewHealthCore
import Foundation
import HealthKit

actor HealthKitClient {
    private let store = HKHealthStore()

    static let approvedReadTypes: Set<HKObjectType> = {
        var types = Set<HKObjectType>()
        let quantityIdentifiers: [HKQuantityTypeIdentifier] = [
            .bloodGlucose,
            .heartRateVariabilitySDNN,
            .restingHeartRate,
            .activeEnergyBurned,
            .stepCount,
            .appleStandTime,
        ]
        quantityIdentifiers.compactMap(HKObjectType.quantityType(forIdentifier:)).forEach {
            types.insert($0)
        }
        if let sleep = HKObjectType.categoryType(forIdentifier: .sleepAnalysis) {
            types.insert(sleep)
        }
        types.insert(HKObjectType.workoutType())
        types.insert(HKObjectType.activitySummaryType())
        return types
    }()

    func requestAuthorization() async throws {
        try await store.requestAuthorization(toShare: [], read: Self.approvedReadTypes)
    }

    func readSamples(since startDate: Date, until endDate: Date) async throws -> [HealthSampleDTO] {
        var samples: [HealthSampleDTO] = []
        samples += try await readQuantity(.bloodGlucose, kind: .bloodGlucose, unit: glucoseUnit, since: startDate, until: endDate)
        samples += try await readQuantity(.heartRateVariabilitySDNN, kind: .heartRateVariability, unit: .secondUnit(with: .milli), since: startDate, until: endDate)
        samples += try await readQuantity(.restingHeartRate, kind: .restingHeartRate, unit: HKUnit.count().unitDivided(by: .minute()), since: startDate, until: endDate)
        samples += try await readQuantity(.activeEnergyBurned, kind: .activeEnergy, unit: .kilocalorie(), since: startDate, until: endDate)
        samples += try await readQuantity(.stepCount, kind: .stepCount, unit: .count(), since: startDate, until: endDate)
        samples += try await readQuantity(.appleStandTime, kind: .standHours, unit: .hour(), since: startDate, until: endDate)
        samples += try await readSleep(since: startDate, until: endDate)
        samples += try await readWorkouts(since: startDate, until: endDate)
        return samples
    }

    private var glucoseUnit: HKUnit {
        HKUnit.gramUnit(with: .milli).unitDivided(by: .literUnit(with: .deci))
    }

    private func readQuantity(
        _ identifier: HKQuantityTypeIdentifier,
        kind: HealthDataKind,
        unit: HKUnit,
        since startDate: Date,
        until endDate: Date
    ) async throws -> [HealthSampleDTO] {
        guard let type = HKObjectType.quantityType(forIdentifier: identifier) else { return [] }
        let healthSamples = try await samples(type: type, since: startDate, until: endDate)
        return healthSamples.compactMap { sample in
            guard let quantity = sample as? HKQuantitySample else { return nil }
            return HealthSampleDTO(
                sampleID: quantity.uuid,
                kind: kind,
                startAt: quantity.startDate,
                endAt: quantity.endDate,
                value: quantity.quantity.doubleValue(for: unit),
                unit: unit.unitString,
                source: quantity.sourceRevision.source.bundleIdentifier,
                device: quantity.device?.name
            )
        }
    }

    private func readSleep(since startDate: Date, until endDate: Date) async throws -> [HealthSampleDTO] {
        guard let type = HKObjectType.categoryType(forIdentifier: .sleepAnalysis) else { return [] }
        let healthSamples = try await samples(type: type, since: startDate, until: endDate)
        return healthSamples.compactMap { sample in
            guard let category = sample as? HKCategorySample,
                  let kind = sleepKind(category.value)
            else { return nil }
            return HealthSampleDTO(
                sampleID: category.uuid,
                kind: kind,
                startAt: category.startDate,
                endAt: category.endDate,
                value: category.endDate.timeIntervalSince(category.startDate),
                unit: "s",
                source: category.sourceRevision.source.bundleIdentifier,
                device: category.device?.name
            )
        }
    }

    private func sleepKind(_ value: Int) -> HealthDataKind? {
        switch HKCategoryValueSleepAnalysis(rawValue: value) {
        case .asleepCore: .sleepCore
        case .asleepDeep: .sleepDeep
        case .asleepREM: .sleepREM
        case .asleep, .asleepUnspecified: .sleepAsleep
        default: nil
        }
    }

    private func readWorkouts(since startDate: Date, until endDate: Date) async throws -> [HealthSampleDTO] {
        let healthSamples = try await samples(type: .workoutType(), since: startDate, until: endDate)
        return healthSamples.compactMap { sample in
            guard let workout = sample as? HKWorkout else { return nil }
            return HealthSampleDTO(
                sampleID: workout.uuid,
                kind: .workout,
                startAt: workout.startDate,
                endAt: workout.endDate,
                value: workout.duration,
                unit: "s",
                source: workout.sourceRevision.source.bundleIdentifier,
                device: workout.device?.name
            )
        }
    }

    private func samples(type: HKSampleType, since startDate: Date, until endDate: Date) async throws -> [HKSample] {
        try await withCheckedThrowingContinuation { continuation in
            let predicate = HKQuery.predicateForSamples(withStart: startDate, end: endDate)
            let query = HKSampleQuery(
                sampleType: type,
                predicate: predicate,
                limit: HKObjectQueryNoLimit,
                sortDescriptors: [NSSortDescriptor(key: HKSampleSortIdentifierStartDate, ascending: true)]
            ) { _, samples, error in
                if let error {
                    continuation.resume(throwing: error)
                } else {
                    continuation.resume(returning: samples ?? [])
                }
            }
            store.execute(query)
        }
    }
}
