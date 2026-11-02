#pragma once
#include "compiler/compiler.hpp"
namespace anubis {
void validate_resource_profiles(const Json &pack);
Json resolve_resources(const Json &workload, const Json &pack);
} // namespace anubis
