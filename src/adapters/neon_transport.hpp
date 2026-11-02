#pragma once
#include "domain/json.hpp"
namespace anubis {
Json neon_target();
Json submit_neon(const Json &target, const Json &payload);
} // namespace anubis
