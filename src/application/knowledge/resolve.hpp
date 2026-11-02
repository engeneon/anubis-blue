#pragma once
#include "compiler/compiler.hpp"
#include <functional>
namespace anubis {
Json resolve_knowledge(const std::string &root_digest,
                       const std::function<Json(const std::string &)> &fetch);
}
