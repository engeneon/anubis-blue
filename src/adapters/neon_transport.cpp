#include "adapters/neon_transport.hpp"
#include <fstream>
#include <httplib/httplib.h>
#include <regex>
namespace anubis {
Json neon_target() {
  const auto *path = std::getenv("ANUBIS_NEON_TARGET");
  if (!path)
    throw Error("target_unqualified",
                "Configure an explicitly reviewed local downstream design tool target or use manual handoff", "",
                409);
  std::ifstream f(path);
  require(bool(f), "target_configuration", "Target profile unavailable");
  auto target = parse(std::string(std::istreambuf_iterator<char>(f), {}));
  keys(target, {"id", "base_url", "api_version", "contract_evidence_sha256", "mode"}, "/target");
  require(
      std::regex_match(text(target, "base_url"), std::regex("http://127\\.0\\.0\\.1:[0-9]{4,5}")),
      "target_address", "Only an administrator-configured loopback target is supported");
  require(text(target, "mode") == "stateless_local_experimental", "target_mode",
          "Only stateless experimental compilation is supported");
  require(text(target, "contract_evidence_sha256").size() == 64, "target_evidence",
          "Reviewed compatibility evidence digest required");
  require(text(target, "api_version") == "1.1.0", "target_version", "Unsupported downstream design tool API version");
  return target;
}
Json submit_neon(const Json &target, const Json &payload) {
  httplib::Client client(text(target, "base_url"));
  client.set_connection_timeout(3);
  client.set_read_timeout(45);
  client.set_write_timeout(10);
  client.set_follow_location(false);
  httplib::Headers headers;
  if (const auto *token = std::getenv("ANUBIS_NEON_TOKEN"))
    headers.emplace("Authorization", std::string("Bearer ") + token);
  auto capabilities = client.Get("/api/v1/capabilities", headers);
  if (!capabilities || capabilities->status != 200)
    throw Error("target_unavailable", "downstream design tool capability check failed before submission");
  auto cap = parse(capabilities->body);
  require(cap.value("api_version", "") == text(target, "api_version"), "target_version_changed",
          "downstream design tool API version changed; requalify target");
  auto response = client.Post("/api/v1/compiler-runs/reference-architecture", headers,
                              payload.dump(), "application/json");
  if (!response)
    throw Error("outcome_unknown", "downstream design tool response was lost; automatic resubmission is disabled");
  if (response->body.size() > 32 * 1024 * 1024)
    throw Error("outcome_unknown",
                "downstream design tool response exceeds import limit; inspect target before reconciliation");
  Json result;
  try {
    result = parse(response->body);
  } catch (const std::exception &) {
    throw Error("outcome_unknown",
                "downstream design tool response was not valid JSON; inspect target before reconciliation");
  }
  return {{"http_status", response->status},
          {"response", result},
          {"target", target},
          {"target_capabilities", cap},
          {"response_digest", digest(result)},
          {"transport_status", response->status == 200 ? "response_received" : "rejected"}};
}
} // namespace anubis
