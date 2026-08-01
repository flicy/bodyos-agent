import Foundation

struct BridgeConfiguration: Codable, Equatable {
    let baseURL: URL
    let deviceBindingID: UUID
    let consentID: UUID
}

final class ConsentStore {
    private let defaults: UserDefaults
    private let configurationKey = "fitcrew.bridge.configuration"
    private let lastSyncKey = "fitcrew.bridge.last-sync"

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
    }

    var configuration: BridgeConfiguration? {
        get {
            guard let data = defaults.data(forKey: configurationKey) else { return nil }
            return try? JSONDecoder().decode(BridgeConfiguration.self, from: data)
        }
        set {
            defaults.set(try? JSONEncoder().encode(newValue), forKey: configurationKey)
        }
    }

    var lastSync: Date? {
        get { defaults.object(forKey: lastSyncKey) as? Date }
        set { defaults.set(newValue, forKey: lastSyncKey) }
    }
}
