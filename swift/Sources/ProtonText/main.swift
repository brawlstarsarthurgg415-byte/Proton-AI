import Foundation

struct CorpusReport: Codable {
    let characters: Int
    let words: Int
    let uniqueWords: Int
    let repeatedWords: Int
    let repetitionRatio: Double
    let topWords: [(word: String, count: Int)]

    enum CodingKeys: String, CodingKey {
        case characters, words
        case uniqueWords = "unique_words"
        case repeatedWords = "repeated_words"
        case repetitionRatio = "repetition_ratio"
        case topWords = "top_words"
    }
}

enum CorpusError: Error, LocalizedError {
    case empty
    var errorDescription: String? { "Corpus is empty." }
}

func tokenize(_ text: String) -> [String] {
    text.folding(options: [.caseInsensitive, .diacriticInsensitive], locale: Locale(identifier: "en_US_POSIX"))
        .split { !$0.isLetter && !$0.isNumber && $0 != "_" }
        .map(String.init)
}

func analyze(_ text: String) throws -> CorpusReport {
    guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
        throw CorpusError.empty
    }
    let tokens = tokenize(text)
    let counts = Dictionary(tokens.map { ($0, 1) }, uniquingKeysWith: +)
    let ordered = counts.sorted {
        $0.value == $1.value ? $0.key < $1.key : $0.value > $1.value
    }.prefix(10).map { (word: $0.key, count: $0.value) }
    let unique = counts.count
    return CorpusReport(
        characters: text.count,
        words: tokens.count,
        uniqueWords: unique,
        repeatedWords: tokens.count - unique,
        repetitionRatio: tokens.isEmpty ? 0 : 1 - Double(unique) / Double(tokens.count),
        topWords: ordered
    )
}

let arguments = Array(CommandLine.arguments.dropFirst())
if arguments.isEmpty {
    print("Usage: proton-text <text>")
    exit(EXIT_SUCCESS)
}
let input = arguments.joined(separator: " ")
do {
    let report = try analyze(input)
    print("Characters: \(report.characters)")
    print("Words: \(report.words)")
    print("Unique words: \(report.uniqueWords)")
    print(String(format: "Repetition: %.3f", report.repetitionRatio))
    for item in report.topWords {
        print("\(item.word): \(item.count)")
    }
} catch {
    fputs("Corpus error: \(error.localizedDescription)\n", stderr)
    exit(EXIT_FAILURE)
}
