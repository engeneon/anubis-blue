#pragma once
#include <nlohmann/json.hpp>
#include <stdexcept>
#include <string>
namespace anubis {
using Json = nlohmann::json;
struct Error : std::runtime_error {
  std::string code, path;
  int status;
  Error(std::string c, std::string m, std::string p = "", int s = 422)
      : runtime_error(m), code(c), path(p), status(s) {}
};
std::string digest(const Json &value);
Json parse(const std::string &text);
void require(bool ok, const std::string &code, const std::string &message,
             const std::string &path = "");
void keys(const Json &j, std::initializer_list<const char *> allowed, const std::string &path);
std::string text(const Json &j, const std::string &key, const std::string &path = "");
Json error_json(const Error &e);
} // namespace anubis
