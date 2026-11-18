// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "ProtonText",
    products: [.executable(name: "proton-text", targets: ["ProtonText"])],
    targets: [.executableTarget(name: "ProtonText")]
)
