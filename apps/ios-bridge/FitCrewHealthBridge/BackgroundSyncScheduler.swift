import BackgroundTasks
import Foundation

@MainActor
final class BackgroundSyncScheduler {
    static let shared = BackgroundSyncScheduler()
    private let identifier = "com.fitcrew.healthbridge.daily-sync"
    private var model: BridgeViewModel?

    func register(model: BridgeViewModel) {
        self.model = model
        BGTaskScheduler.shared.register(forTaskWithIdentifier: identifier, using: nil) { task in
            guard let processingTask = task as? BGProcessingTask else {
                task.setTaskCompleted(success: false)
                return
            }
            Task { @MainActor in
                processingTask.expirationHandler = {}
                await model.sync(fullReconciliation: false)
                processingTask.setTaskCompleted(success: true)
            }
        }
    }

    func schedule() {
        let request = BGProcessingTaskRequest(identifier: identifier)
        request.requiresNetworkConnectivity = true
        request.earliestBeginDate = Calendar.current.date(byAdding: .hour, value: 20, to: Date())
        try? BGTaskScheduler.shared.submit(request)
    }
}
