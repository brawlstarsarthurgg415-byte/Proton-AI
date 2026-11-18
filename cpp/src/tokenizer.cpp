#include "proton/tokenizer.hpp"
#include <cctype>
namespace proton {
std::vector<std::string> tokenize_ascii(const std::string& input) {
    std::vector<std::string> out; std::string word;
    for (unsigned char c : input) {
        if (std::isalnum(c) || c >= 128) word.push_back(static_cast<char>(std::tolower(c)));
        else if (!word.empty()) { out.push_back(word); word.clear(); }
    }
    if (!word.empty()) out.push_back(word);
    return out;
}
}
