#pragma once
#include "compiler/compiler.hpp"
namespace anubis {
Json planning_catalog();
void validate_planning(const Json &w);
void add_planning(const Json &w, Json &result);
}
