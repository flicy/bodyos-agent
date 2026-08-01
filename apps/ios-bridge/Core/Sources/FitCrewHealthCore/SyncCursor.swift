public struct SyncCursor: Equatable, Sendable {
    public private(set) var value: String?

    public init(value: String?) {
        self.value = value
    }

    public mutating func recordUploadResult(success: Bool, proposedValue: String) {
        guard success else { return }
        value = proposedValue
    }
}
