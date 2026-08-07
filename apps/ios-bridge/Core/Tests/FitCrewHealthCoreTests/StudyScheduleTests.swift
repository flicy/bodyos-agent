import Foundation
import Testing
@testable import FitCrewHealthCore

@Test func studyRequestsOneFullReconciliationOnDay16() throws {
    var calendar = Calendar(identifier: .gregorian)
    calendar.timeZone = try #require(TimeZone(identifier: "Asia/Shanghai"))
    let start = try #require(ISO8601DateFormatter().date(from: "2026-08-01T08:00:00+08:00"))
    let day15 = try #require(calendar.date(byAdding: .day, value: 14, to: start))
    let day16 = try #require(calendar.date(byAdding: .day, value: 15, to: start))

    #expect(
        !StudySchedule.requiresFullReconciliation(
            startedAt: start,
            lastFullReconciliation: nil,
            now: day15,
            calendar: calendar
        )
    )
    #expect(
        StudySchedule.requiresFullReconciliation(
            startedAt: start,
            lastFullReconciliation: nil,
            now: day16,
            calendar: calendar
        )
    )
    #expect(
        !StudySchedule.requiresFullReconciliation(
            startedAt: start,
            lastFullReconciliation: day16,
            now: day16,
            calendar: calendar
        )
    )
}
