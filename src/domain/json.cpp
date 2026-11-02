#include "domain/json.hpp"
#include <set>

#include <iomanip>
#include <openssl/evp.h>
#include <sstream>
namespace anubis {
void require(bool ok, const std::string &c, const std::string &m, const std::string &p) {
  if (!ok)
    throw Error(c, m, p);
}
std::string digest(const Json &j) {
  auto s = j.dump(-1, ' ', false, Json::error_handler_t::strict);
  unsigned char out[EVP_MAX_MD_SIZE];
  unsigned n = 0;
  if (EVP_Digest(s.data(), s.size(), out, &n, EVP_sha256(), nullptr) != 1)
    throw std::runtime_error("SHA256 failure");
  std::ostringstream h;
  for (unsigned i = 0; i < n; i++)
    h << std::hex << std::setw(2) << std::setfill('0') << int(out[i]);
  return h.str();
}
Json parse(const std::string &s) {
  try {
    std::vector<std::set<std::string>> objects;
    auto cb = [&](int depth, Json::parse_event_t event, Json &parsed) {
      require(depth <= 64, "depth_limit", "JSON exceeds nesting limit");
      if (event == Json::parse_event_t::object_start)
        objects.emplace_back();
      if (event == Json::parse_event_t::key &&
          !objects.back().insert(parsed.get<std::string>()).second)
        throw Error("duplicate_key", "Duplicate JSON key");
      if (event == Json::parse_event_t::object_end)
        objects.pop_back();
      return true;
    };
    return Json::parse(s, cb);
  } catch (const Error &) {
    throw;
  } catch (const std::exception &) {
    throw Error("invalid_json", "Malformed JSON document");
  }
}
void keys(const Json &j, std::initializer_list<const char *> allowed, const std::string &path) {
  require(j.is_object(), "type", "Expected object", path);
  for (auto it = j.begin(); it != j.end(); ++it) {
    bool found = false;
    for (auto a : allowed)
      if (it.key() == a)
        found = true;
    require(found, "unknown_field", "Unsupported field: " + it.key(), path + "/" + it.key());
  }
}
std::string text(const Json &j, const std::string &k, const std::string &p) {
  require(j.contains(k) && j[k].is_string(), "required", "Expected string", p + "/" + k);
  return j[k].get<std::string>();
}
Json error_json(const Error &e) {
  return {
      {"error",
       {{"code", e.code},
        {"message", e.what()},
        {"path", e.path},
        {"retryable", e.status == 503},
        {"remediation", "Review the field or operation and retry with the current revision."}}}};
}
} // namespace anubis
