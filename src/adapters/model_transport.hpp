#pragma once
#include "domain/json.hpp"
namespace anubis {
void validate_model_profile(const Json&);
Json execute_model(const Json&,const Json&);
Json execute_mcp(const Json&,const std::string&,const Json&);
}
