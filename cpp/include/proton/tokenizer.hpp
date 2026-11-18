#pragma once

#include <cstddef>
#include <string>
#include <unordered_map>
#include <vector>

namespace proton {
struct TextStats {
    std::size_t bytes{};
    std::size_t words{};
    std::size_t unique_words{};
    std::size_t repeated_words{};
    double repetition_ratio{};
};

std::vector<std::string> tokenize_ascii(const std::string& input);
TextStats analyze_ascii(const std::string& input);
std::unordered_map<std::string, std::size_t> word_frequencies(const std::string& input);
}
