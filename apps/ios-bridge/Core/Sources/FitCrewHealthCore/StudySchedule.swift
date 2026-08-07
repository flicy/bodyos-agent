import Foundation

public enum StudySchedule {
    public static func requiresFullReconciliation(
        startedAt: Date,
        lastFullReconciliation: Date?,
        now: Date,
        calendar: Calendar = .current
    ) -> Bool {
        guard lastFullReconciliation == nil,
              let day16 = calendar.date(byAdding: .day, value: 15, to: startedAt)
        else { return false }
        return now >= day16
    }
}
