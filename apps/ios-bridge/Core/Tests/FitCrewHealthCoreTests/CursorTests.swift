import Testing
@testable import FitCrewHealthCore

@Test func cursorAdvancesOnlyAfterSuccessfulUpload() {
    var cursor = SyncCursor(value: "before")

    cursor.recordUploadResult(success: false, proposedValue: "after-failure")
    #expect(cursor.value == "before")

    cursor.recordUploadResult(success: true, proposedValue: "after-success")
    #expect(cursor.value == "after-success")
}
