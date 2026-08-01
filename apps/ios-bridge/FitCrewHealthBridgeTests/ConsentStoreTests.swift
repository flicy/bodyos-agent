import Foundation
import Testing
@testable import FitCrewHealthBridge

@Test func configurationRoundTripsWithoutDeviceSecret() throws {
    let suite = "fitcrew-health-bridge-tests-\(UUID().uuidString)"
    let defaults = try #require(UserDefaults(suiteName: suite))
    defaults.removePersistentDomain(forName: suite)
    let store = ConsentStore(defaults: defaults)
    let configuration = BridgeConfiguration(
        baseURL: URL(string: "https://owner.example")!,
        deviceBindingID: UUID(uuidString: "22222222-2222-4222-8222-222222222222")!,
        consentIDs: [
            "blood_glucose": UUID(
                uuidString: "33333333-3333-4333-8333-333333333333"
            )!,
        ]
    )

    store.configuration = configuration

    #expect(store.configuration == configuration)
}
