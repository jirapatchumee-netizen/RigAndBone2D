// swift-tools-version: 6.0
import PackageDescription
let package = Package(name: "RigAndBone2D", platforms: [.macOS(.v14)], products: [.executable(name: "RigAndBone2D", targets: ["RigAndBone2D"])], targets: [.executableTarget(name: "RigAndBone2D", swiftSettings: [.swiftLanguageMode(.v5)])])
