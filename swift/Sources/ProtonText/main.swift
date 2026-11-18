import Foundation

/// Simple Unicode-aware word splitting for the Swift adapter.
func tokenize(_ text: String) -> [String] {
    text.lowercased().split { !$0.isLetter && !$0.isNumber && $0 != "_" }.map(String.init)
}

let input = CommandLine.arguments.dropFirst().joined(separator: " ")
if input.isEmpty {
    print("Usage: proton-text <text>")
} else {
    print(tokenize(input).joined(separator: "\n"))
}
