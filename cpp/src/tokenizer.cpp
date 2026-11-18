#include "proton/tokenizer.hpp"

#include <algorithm>
#include <cctype>
#include <utility>

namespace proton {
std::vector<std::string> tokenize_ascii(const std::string& input) {
    std::vector<std::string> output;
    std::string word;
    for (unsigned char character : input) {
        if (std::isalnum(character) || character == '_') {
            word.push_back(static_cast<char>(std::tolower(character)));
        } else if (!word.empty()) {
            output.push_back(std::move(word));
            word.clear();
        }
    }
    if (!word.empty()) output.push_back(std::move(word));
    return output;
}

std::unordered_map<std::string, std::size_t> word_frequencies(const std::string& input) {
    std::unordered_map<std::string, std::size_t> counts;
    for (const auto& token : tokenize_ascii(input)) ++counts[token];
    return counts;
}

TextStats analyze_ascii(const std::string& input) {
    const auto tokens = tokenize_ascii(input);
    const auto frequencies = word_frequencies(input);
    std::size_t repeated = 0;
    for (const auto& item : frequencies) {
        if (item.second > 1) repeated += item.second - 1;
    }
    const auto unique = frequencies.size();
    const double ratio = tokens.empty() ? 0.0
        : 1.0 - static_cast<double>(unique) / static_cast<double>(tokens.size());
    return TextStats{input.size(), tokens.size(), unique, repeated, ratio};
}
}
