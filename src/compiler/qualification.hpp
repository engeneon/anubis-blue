#pragma once
#include "domain/quantity.hpp"
namespace anubis {
Json validate_protocol(const Json &protocol);
Json evaluate_qualification(const Json &protocol, const Json &dataset);
} // namespace anubis
