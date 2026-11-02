#include "compiler/resources.hpp"
#include <set>
namespace anubis {
void validate_resource_profiles(const Json &pack) {
  auto records = pack.value("resource_profiles", Json::array());
  require(records.is_array() && records.size() <= 256, "resource_profiles",
          "At most 256 resource profiles");
  std::set<std::string> ids;
  for (const auto &p : records) {
    keys(p,
         {"id", "kind", "vendor", "product", "configuration", "fingerprint", "protocols",
          "usable_bytes", "read_Bps", "write_Bps", "line_Bps", "latency_seconds", "source",
          "evidence_basis", "scope"},
         "/resource_profiles");
    require(ids.insert(text(p, "id")).second, "duplicate", "Duplicate resource evidence ID");
    require(p.dump().size() <= 32768, "profile_limit", "Resource profile exceeds 32 KiB");
    auto kind = text(p, "kind");
    require(kind == "storage" || kind == "network", "resource_kind",
            "Storage or network profile required");
    for (auto k : {"vendor", "product", "configuration", "source", "scope"})
      require(!text(p, k).empty(), "required", "Profile field required", k);
    require(p.contains("fingerprint") && p["fingerprint"].is_object() && !p["fingerprint"].empty(),
            "fingerprint", "Resource configuration applicability required");
    require(p.contains("protocols") && p["protocols"].is_array(), "protocols",
            "Protocol list required");
    for (const auto &protocol : p["protocols"])
      require(protocol.is_string(), "protocol", "Protocol name must be a string");
    for (auto k : {"usable_bytes", "read_Bps", "write_Bps", "line_Bps", "latency_seconds"})
      if (p.contains(k))
        require(Rational::decimal(text(p, k)) >= Rational(0), "negative",
                "Negative resource capacity");
    auto basis = text(p, "evidence_basis");
    require(basis == "synthetic" || basis == "measured" || basis == "reference_derived",
            "evidence_basis", "Unsupported resource evidence basis");
    if (pack["channel"] == "qualified") {
      require(basis != "synthetic", "synthetic_evidence",
              "Qualified pack cannot include synthetic resource evidence");
      bool source = false;
      for (const auto &s : pack.value("sources", Json::array()))
        if (s.value("id", "") == text(p, "source")) {
          require(s.value("configuration_digest", "") == digest(p["fingerprint"]),
                  "source_configuration", "Resource source configuration mismatch");
          require(text(s, "sha256").size() == 64 && !text(s, "license").empty() &&
                      !text(s, "uri").empty(),
                  "source", "Attributable source artifact required");
          source = true;
        }
      require(source, "source_missing", "Resource evidence source missing");
    }
  }
}
Json resolve_resources(const Json &w, const Json &pack) {
  Json result = Json::array();
  const auto limit = w.value("candidate_limit", 256);
  bool truncated = false;
  for (const auto &sc : w["scenarios"])
    for (const auto &s : w["stages"]) {
      auto id = text(s, "id"), type = text(s, "type");
      if (type != "data" && type != "transfer")
        continue;
      if (sc.contains("active_stages") &&
          std::find(sc["active_stages"].begin(), sc["active_stages"].end(), id) ==
              sc["active_stages"].end())
        continue;
      auto q = [&](const std::string &key, const std::string &dim) -> std::optional<Rational> {
        if (!s["observations"].contains(key))
          return {};
        return quantity(s["observations"][key], dim, "/stages/" + id + "/" + key);
      };
      for (const auto &p : pack.value("resource_profiles", Json::array())) {
        if (p["kind"] != (type == "data" ? "storage" : "network"))
          continue;
        if (result.size() >= static_cast<size_t>(limit)) {
          truncated = true;
          continue;
        }
        Json checks = Json::array();
        std::string status = "pass";
        auto check = [&](const std::string &name, const std::string &state,
                         const std::string &reason) {
          checks.push_back({{"name", name}, {"status", state}, {"reason", reason}});
          if (state == "fail")
            status = "fail";
          else if (state == "unknown" && status != "fail")
            status = "unknown";
        };
        if (!s.contains("resource_fingerprint") || s["resource_fingerprint"] != p["fingerprint"])
          check(
              "applicability", "unknown",
              "No exact workload/configuration match; absence of evidence is not vendor exclusion");
        if (!s.contains("protocols") || s["protocols"].empty())
          check("protocols", "unknown", "Required access protocol not specified");
        else
          for (const auto &protocol : s["protocols"])
            check("protocol:" + protocol.get<std::string>(),
                  std::find(p["protocols"].begin(), p["protocols"].end(), protocol) !=
                          p["protocols"].end()
                      ? "pass"
                      : "fail",
                  "Exact product configuration protocol evidence");
        auto capacity = [&](const std::string &field, std::optional<Rational> demand) {
          if (!demand || !p.contains(field))
            check(field, "unknown", "Demand or matching capacity evidence missing");
          else
            check(field, Rational::decimal(text(p, field)) >= *demand ? "pass" : "fail",
                  "Measured/reference capacity at this exact product configuration; no "
                  "extrapolation");
        };
        if (type == "data") {
          auto bytes = q("bytes", "bytes"), free = q("free_fraction", "ratio");
          capacity("usable_bytes",
                   bytes && free ? std::optional(*bytes / (Rational(1) - *free)) : std::nullopt);
          capacity("read_Bps", q("read_rate", "byte_rate"));
          capacity("write_Bps", q("write_rate", "byte_rate"));
        } else {
          auto bytes = q("bytes", "bytes"), window = q("window", "time"),
               eff = q("protocol_efficiency", "ratio"), util = q("utilization", "ratio");
          capacity("line_Bps",
                   bytes && window && eff && util
                       ? std::optional(*bytes * Rational::decimal(sc.value("multiplier", "1")) /
                                       *window / *eff / *util)
                       : std::nullopt);
          check("latency", "unknown",
                "Transfer-window bandwidth does not establish RTT or end-to-end latency");
        }
        result.push_back({{"id", id + ":" + text(sc, "id") + ":" + text(p, "id")},
                          {"stage_id", id},
                          {"scenario_id", sc["id"]},
                          {"kind", p["kind"]},
                          {"vendor", p["vendor"]},
                          {"product", p["product"]},
                          {"configuration", p["configuration"]},
                          {"status", status},
                          {"constraints", checks},
                          {"evidence_id", p["id"]},
                          {"source", p["source"]},
                          {"evidence_channel", pack["channel"]},
                          {"scope", "Per-stage product configuration assessment; shared use "
                                    "requires joint qualification"}});
      }
    }
  std::sort(result.begin(), result.end(),
            [](const Json &a, const Json &b) { return a["id"] < b["id"]; });
  return {{"candidates", result},
          {"search",
           {{"limit", limit},
            {"evaluated", result.size()},
            {"truncated", truncated},
            {"optimality", "not_claimed"}}}};
}
} // namespace anubis
