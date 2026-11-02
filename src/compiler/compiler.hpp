#pragma once
#include "domain/quantity.hpp"
namespace anubis {
inline constexpr auto engine_version = "0.1.0";
Json validate_workload(const Json &workload);
Json normalize_workload(const Json &workload);
Json validate_pack(const Json &pack);
Json compile(const Json &workload, const Json &pack);
Json capabilities();
Json component_descriptors();
Json project(const Json &result, const Json &request);
Json assess(const Json &projection, const Json &external);
} // namespace anubis
