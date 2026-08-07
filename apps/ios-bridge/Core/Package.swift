// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "FitCrewHealthCore",
    platforms: [.iOS(.v17), .macOS(.v13)],
    products: [
        .library(name: "FitCrewHealthCore", targets: ["FitCrewHealthCore"]),
    ],
    targets: [
        .target(name: "FitCrewHealthCore"),
        .testTarget(name: "FitCrewHealthCoreTests", dependencies: ["FitCrewHealthCore"]),
    ]
)
