#pragma once
#include <ranges>
#include <string>
#include <algorithm>

namespace util {
    inline auto convertSpaceToNewLine = [](std::string&& str) {
        std::string result{std::move(str)};
        std::ranges::replace(result.begin(), result.end(), ' ', '\n');
        result = result.substr(1, result.size()-2);
        return result;
    };
}
