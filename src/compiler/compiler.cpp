#include "compiler/compiler.hpp"
#include "compiler/planning.hpp"
#include "compiler/resolution.hpp"
#include "compiler/resources.hpp"
#include <algorithm>
#include <functional>
#include <regex>
#include <set>
namespace anubis {
static const std::map<std::string, std::string> dimensions = {{"calls_per_job", "ratio"},
                                                              {"branch_probability", "ratio"},
                                                              {"fanout", "count"},
                                                              {"retry_probability", "ratio"},
                                                              {"max_retries", "count"},
                                                              {"users", "count"},
                                                              {"interval", "time"},
                                                              {"rate", "rate"},
                                                              {"extra_calls", "ratio"},
                                                              {"input_tokens", "token"},
                                                              {"output_tokens", "token"},
                                                              {"jobs", "count"},
                                                              {"window", "time"},
                                                              {"tokens", "token"},
                                                              {"effective_fraction", "ratio"},
                                                              {"explicit_overhead", "time"},
                                                              {"bytes", "bytes"},
                                                              {"free_fraction", "ratio"},
                                                              {"checkpoint_bytes", "bytes"},
                                                              {"save_window", "time"},
                                                              {"recent", "count"},
                                                              {"daily", "count"},
                                                              {"retention_overlap", "count"},
                                                              {"protocol_efficiency", "ratio"},
                                                              {"utilization", "ratio"},
                                                              {"read_rate", "byte_rate"},
                                                              {"write_rate", "byte_rate"},
                                                              {"cpu_seconds", "time"},
                                                              {"host_bytes", "bytes"},
                                                              {"local_bytes", "bytes"}};
static std::optional<Rational> q(const Json &s, const std::string &k) {
  if (!s.contains("observations") || !s["observations"].contains(k))
    return {};
  return quantity(s["observations"][k], dimensions.at(k),
                  "/stages/" + s.value("id", "") + "/observations/" + k);
}
static int integer(const Json &j, const std::string &key, int fallback, int max) {
  if (!j.contains(key))
    return fallback;
  require(j[key].is_number_integer(), "integer", "Expected integer", key);
  auto n = j[key].get<int64_t>();
  require(n >= 0 && n <= max, "range", "Integer outside allowed range", key);
  return static_cast<int>(n);
}
static bool supported(const std::string &t) {
  return t == "inference" || t == "batch" || t == "training" || t == "transfer" || t == "data" ||
         t == "checkpoint" || t == "cpu";
}
Json validate_workload(const Json &w) {
  keys(w,
       {"schema_version", "name", "stages", "edges", "scenarios", "tenancy", "notes", "objective",
        "candidate_limit", "planning", "characterization"},
       "");
  if(w.contains("characterization")) require(w["characterization"].is_object(),"characterization","Characterization must be an object");
  require(text(w, "schema_version") == "1.0", "version", "Unsupported workload schema");
  require(!text(w, "name").empty() && text(w, "name").size() <= 240, "name",
          "Name length must be 1–240");
  require(w.contains("stages") && w["stages"].is_array() && w["stages"].size() <= 128, "stages",
          "Expected at most 128 stages");
  require(w.contains("scenarios") && w["scenarios"].is_array() && !w["scenarios"].empty() &&
              w["scenarios"].size() <= 32,
          "scenarios", "One to 32 explicit scenarios required");
  integer(w, "candidate_limit", 256, 4096);
  std::set<std::string> ids;
  Json diagnostics = Json::array();
  for (const auto &s : w["stages"]) {
    keys(s,
         {"id", "name", "type", "model", "runtime", "precision", "fingerprint", "observations",
          "storage_tier", "platforms", "notes", "service_objectives", "protocols",
          "resource_fingerprint", "planning"},
         "/stages");
    auto id = text(s, "id");
    require(std::regex_match(id, std::regex("[A-Za-z0-9_-]{1,80}")), "identifier",
            "Use 1–80 letters, digits, underscores or hyphens for identifiers");
    if (s.contains("notes"))
      require(text(s, "notes").size() <= 16384, "text_limit", "Notes exceed 16 KiB");
    require(!id.empty() && id.size() <= 80 && ids.insert(id).second, "stage_id",
            "Stage IDs must be unique");
    auto t = text(s, "type");
    if (s.contains("protocols")) {
      require(s["protocols"].is_array(), "protocols", "Expected protocol list");
      for (const auto &p : s["protocols"])
        require(p.is_string(), "protocol", "Expected protocol name");
    }
    if (s.contains("resource_fingerprint"))
      require(s["resource_fingerprint"].is_object(), "fingerprint",
              "Expected configuration fingerprint");
    for (const auto &slo : s.value("service_objectives", Json::array())) {
      keys(slo, {"metric", "percentile", "target", "boundary"}, "/service_objectives");
      auto metric = text(slo, "metric");
      require(metric == "ttft" || metric == "inter_token_latency" || metric == "completion",
              "slo_metric", "Unsupported latency metric");
      auto percentile = Rational::decimal(text(slo, "percentile"));
      require(percentile > Rational(0) && percentile <= Rational(100), "percentile",
              "Percentile must be in (0,100]");
      require(!text(slo, "boundary").empty(), "boundary", "Latency boundary required");
      auto target = quantity(slo.at("target"), "time", "/service_objectives/target");
      if (!target)
        diagnostics.push_back({{"code", "unresolved_slo"},
                               {"path", "/stages/" + id},
                               {"message", "Service objective target is unresolved"}});
    }
    if (!supported(t))
      diagnostics.push_back({{"code", "unsupported_stage"},
                             {"path", "/stages/" + id},
                             {"message", "Description retained; no evaluator for " + t}});
    require(s.contains("observations") && s["observations"].is_object(), "observations",
            "Observation map required");
    for (auto it = s["observations"].begin(); it != s["observations"].end(); ++it) {
      require(dimensions.contains(it.key()), "field", "Unknown observation", it.key());
      auto v = quantity(it.value(), dimensions.at(it.key()), id + "/" + it.key());
      if (v && dimensions.at(it.key()) == "count")
        require(v->den() == 1, "integer", "Count must be integral", id + "/" + it.key());
      if (v && (it.key() == "effective_fraction" || it.key() == "protocol_efficiency" ||
                it.key() == "utilization"))
        require(*v > Rational(0) && *v <= Rational(1), "ratio", "Fraction must be in (0,1]",
                it.key());
      if (v && (it.key() == "retry_probability" || it.key() == "branch_probability"))
        require(*v <= Rational(1), "probability", "Probability must be in [0,1]", it.key());
      if (v && it.key() == "max_retries")
        require(*v <= Rational(32), "retry_limit", "At most 32 retries supported", it.key());
      if (v && it.key() == "free_fraction")
        require(*v < Rational(1), "ratio", "Free fraction must be below 1", it.key());
    }
    require(!(q(s, "rate") && q(s, "users")), "double_demand",
            "Choose an arrival rate OR users/interval", id);
    require(!(q(s, "effective_fraction") && q(s, "explicit_overhead")), "double_overhead",
            "Effective fraction and explicit overhead are exclusive", id);
    for (auto f : {"window", "interval", "save_window"})
      if (auto v = q(s, f))
        require(*v > Rational(0), "zero_window", "Window must be positive", id);
  }
  std::set<std::string> scenarios;
  for (const auto &s : w["scenarios"]) {
    keys(s, {"id", "name", "active_stages", "multiplier", "failed_nodes", "cache_state", "notes"},
         "/scenarios");
    auto id = text(s, "id");
    require(std::regex_match(id, std::regex("[A-Za-z0-9_-]{1,80}")), "identifier",
            "Use 1–80 letters, digits, underscores or hyphens for identifiers");
    if (s.contains("notes"))
      require(text(s, "notes").size() <= 16384, "text_limit", "Notes exceed 16 KiB");
    require(scenarios.insert(id).second, "scenario_id", "Duplicate scenario");
    integer(s, "failed_nodes", 0, 64);
    if (s.contains("multiplier"))
      require(Rational::decimal(text(s, "multiplier")) > Rational(0), "multiplier",
              "Multiplier must be positive");
    if (s.contains("active_stages")) {
      require(s["active_stages"].is_array(), "type", "active_stages must be array");
      std::set<std::string> active;
      for (auto a : s["active_stages"]) {
        require(a.is_string() && ids.contains(a.get<std::string>()), "stage_reference",
                "Unknown active stage");
        require(active.insert(a.get<std::string>()).second, "duplicate", "Duplicate active stage");
      }
    }
  }
  require(w.value("tenancy", "single") == "single" || w.value("tenancy", "single") == "multi",
          "tenancy", "Expected single or multi");
  require(w.value("objective", "gpu_count") == "gpu_count", "objective",
          "Only within-platform GPU count ordering supported; cross-platform cost is unqualified");
  // Only acyclic composition is currently admitted. Bounded repetition belongs in stage demand, not
  // opaque loops.
  std::map<std::string, std::vector<std::string>> graph;
  for (const auto &e : w.value("edges", Json::array())) {
    keys(e, {"from", "to"}, "/edges");
    auto a = text(e, "from"), b = text(e, "to");
    require(ids.contains(a) && ids.contains(b), "edge", "Dangling edge");
    graph[a].push_back(b);
  }
  std::set<std::string> visiting, done;
  std::function<void(std::string)> visit = [&](std::string id) {
    require(!visiting.contains(id), "cycle", "Cyclic graphs require an unsupported model");
    if (done.contains(id))
      return;
    visiting.insert(id);
    for (auto b : graph[id])
      visit(b);
    visiting.erase(id);
    done.insert(id);
  };
  for (auto id : ids)
    visit(id);
  validate_planning(w);
  return {{"valid", true},
          {"diagnostics", diagnostics},
          {"description", diagnostics.empty() ? "valid" : "partial"}};
}
Json normalize_workload(const Json &input) {
  validate_workload(input);
  Json w = input;
  for (auto &s : w["stages"]) {
    auto obs = s["observations"];
    for (auto it = obs.begin(); it != obs.end(); ++it) {
      auto n = normalize_quantity(it.value(), it.key());
      if (n.is_null())
        s["observations"].erase(it.key());
      else
        s["observations"][it.key()] = n;
    }
    if (s.contains("service_objectives")) {
      for (auto &slo : s["service_objectives"])
        slo["target"] = normalize_quantity(slo["target"], "/service_objectives/target");
      std::sort(s["service_objectives"].begin(), s["service_objectives"].end(),
                [](const Json &a, const Json &b) { return a.dump() < b.dump(); });
    }
  }
  auto by_id = [](const Json &a, const Json &b) {
    return a["id"].get<std::string>() < b["id"].get<std::string>();
  };
  std::sort(w["stages"].begin(), w["stages"].end(), by_id);
  std::sort(w["scenarios"].begin(), w["scenarios"].end(), by_id);
  for (auto &s : w["scenarios"]) {
    if (s.contains("active_stages"))
      std::sort(s["active_stages"].begin(), s["active_stages"].end());
    if (s.contains("multiplier"))
      s["multiplier"] = Rational::decimal(s["multiplier"]).display(12);
  }
  if (w.contains("edges"))
    std::sort(w["edges"].begin(), w["edges"].end(),
              [](const Json &a, const Json &b) { return a.dump() < b.dump(); });
  return w;
}
Json validate_pack(const Json &p) {
  keys(p,
       {"schema_version", "id", "version", "channel", "dependencies", "profiles", "sources",
        "license", "description", "resource_profiles"},
       "/pack");
  require(text(p, "schema_version") == "1.0", "version", "Unsupported pack schema");
  text(p, "id");
  text(p, "version");
  require(p.value("channel", "") == "synthetic" || p.value("channel", "") == "qualified", "channel",
          "Unknown evidence channel");
  require(p.contains("profiles") && p["profiles"].is_array() && p["profiles"].size() <= 256,
          "profiles", "Expected at most 256 profiles");
  auto dependencies = p.value("dependencies", Json::array());
  require(dependencies.is_array() && dependencies.size() <= 64, "dependencies",
          "At most 64 digest dependencies");
  for (const auto &d : dependencies)
    require(d.is_string() && d.get<std::string>().size() == 64 &&
                d.get<std::string>().find_first_not_of("0123456789abcdef") == std::string::npos,
            "dependency_digest", "Dependency must be a lowercase SHA256 digest");
  validate_resource_profiles(p);
  std::set<std::string> ids;
  for (const auto &f : p["profiles"]) {
    keys(f,
         {"id",
          "platform",
          "kind",
          "fingerprint",
          "gpu_per_node",
          "gpu_per_replica",
          "capacity",
          "admission",
          "memory_required_bytes",
          "hbm_bytes",
          "nodes",
          "host_ram_bytes",
          "local_disk_bytes",
          "cpu_cores",
          "read_Bps",
          "write_Bps",
          "network_Bps",
          "source",
          "evidence_basis",
          "scope",
          "interference_qualified",
          "memory_components"},
         "/profiles");
    require(ids.insert(text(f, "id")).second, "ambiguous_evidence", "Duplicate evidence identity");
    require(std::regex_match(text(f, "id"), std::regex("[A-Za-z0-9_-]{1,128}")), "identifier",
            "Invalid evidence identifier");
    require(f.dump().size() <= 32768, "profile_limit", "A profile must fit within 32 KiB");
    text(f, "platform");
    text(f, "source");
    text(f, "scope");
    auto basis = text(f, "evidence_basis");
    require(basis == "synthetic" || basis == "measured" || basis == "predicted" ||
                basis == "reference_derived",
            "evidence_basis", "Unknown evidence origin");
    if (p["channel"] == "qualified") {
      require(basis != "synthetic", "synthetic_evidence", "Synthetic record in qualified pack");
      bool attributed = false;
      for (auto source : p.value("sources", Json::array()))
        if (source.value("id", "") == text(f, "source")) {
          require(text(source, "sha256").size() == 64, "source_digest",
                  "Source artifact digest required");
          text(source, "license");
          text(source, "uri");
          require(source.value("configuration_digest", "") == digest(f["fingerprint"]),
                  "source_configuration", "Source configuration does not match profile");
          attributed = true;
        }
      require(attributed, "source_missing",
              "Qualified evidence must reference an attributable source");
    }
    if (f.contains("memory_components")) {
      keys(f["memory_components"],
           {"weights", "kv_cache", "workspace", "communication", "runtime", "optimizer",
            "gradients", "activations"},
           "/memory_components");
      Rational sum;
      for (auto it = f["memory_components"].begin(); it != f["memory_components"].end(); ++it) {
        auto value = Rational::decimal(it.value().get<std::string>());
        require(value >= Rational(0), "negative", "Memory component cannot be negative");
        sum = sum + value;
      }
      require(f.contains("memory_required_bytes") &&
                  sum <= Rational::decimal(text(f, "memory_required_bytes")),
              "memory_ledger", "Component subtotal exceeds declared per-device memory total");
    }
    auto kind = text(f, "kind");
    require(kind == "inference" || kind == "training", "profile_kind",
            "Unsupported performance profile");
    require(f.contains("fingerprint") && f["fingerprint"].is_object() && !f["fingerprint"].empty(),
            "fingerprint", "Applicability fingerprint required");
    require(integer(f, "gpu_per_node", 0, 256) > 0, "platform", "GPU per node required");
    require(integer(f, "gpu_per_replica", 0, 256) > 0, "platform", "GPU per replica required");
    for (auto k : {"capacity", "admission", "memory_required_bytes", "hbm_bytes", "host_ram_bytes",
                   "local_disk_bytes", "read_Bps", "write_Bps", "network_Bps"})
      if (f.contains(k)) {
        auto r = Rational::decimal(text(f, k));
        require(r >= Rational(0), "negative", "Negative profile quantity", k);
      }
    require(f.contains("capacity") && Rational::decimal(text(f, "capacity")) > Rational(0),
            "capacity", "Positive qualified capacity required");
    if (f.contains("admission")) {
      auto a = Rational::decimal(text(f, "admission"));
      require(a > Rational(0) && a <= Rational(1), "admission", "Admission fraction outside (0,1]");
    }
    if (f.contains("cpu_cores"))
      require(integer(f, "cpu_cores", 0, 65536) > 0, "cpu_cores",
              "Host CPU count must be positive");
    if (kind == "training")
      require(integer(f, "nodes", 0, 4096) > 0, "nodes", "Measured training node count required");
  }
  return {{"valid", true}, {"digest", digest(p)}, {"profiles", p["profiles"].size()}};
}
struct Facts {
  Json facts = Json::array(), derivations = Json::array(), questions = Json::array();
  void add(std::string stage, std::string scenario, std::string name, Rational v, std::string u,
           std::string rule, Json inputs, Json evidence = Json::array(),
           std::string basis = "derived") {
    std::string display = v.display(9) + " " + u;
    if (u == "B" || u == "B/s") {
      for (auto scale : {std::pair<int64_t, const char *>{1000000000000000LL, "PB"},
                         {1000000000000LL, "TB"},
                         {1000000000LL, "GB"},
                         {1000000LL, "MB"}})
        if (v >= Rational(scale.first)) {
          display = (v / Rational(scale.first)).display(6) + " " + scale.second +
                    (u == "B/s" ? "/s" : "");
          break;
        }
    }
    auto id = stage + ":" + scenario + ":" + name;
    facts.push_back({{"id", id},
                     {"stage_id", stage},
                     {"scenario_id", scenario},
                     {"name", name},
                     {"value", v.display(9)},
                     {"display", display},
                     {"exact", v.exact()},
                     {"unit", u},
                     {"evidence_basis", basis},
                     {"derivation_id", id}});
    derivations.push_back({{"id", id},
                           {"rule", rule},
                           {"version", "1.0"},
                           {"inputs", inputs},
                           {"evidence", evidence},
                           {"result", v.exact()},
                           {"rounding", "exact rational; display half-up to 9 decimals"}});
  }
  void ask(std::string stage, std::string field, std::string message) {
    questions.push_back({{"code", "missing_or_unqualified"},
                         {"stage_id", stage},
                         {"path", "/stages/" + stage + "/" + field},
                         {"message", message}});
  }
};
Json compile(const Json &input, const Json &pack) {
  auto w = normalize_workload(input);
  validate_pack(pack);
  require(pack.value("dependencies", Json::array()).empty(), "unresolved_lock",
          "Compiler requires resolved knowledge");
  Facts out;
  Json candidates = Json::array();
  auto profiles = pack["profiles"];
  std::sort(profiles.begin(), profiles.end(),
            [](const Json &a, const Json &b) { return a["id"] < b["id"]; });
  int limit = integer(w, "candidate_limit", 256, 4096), evaluated = 0;
  bool truncated = false;
  for (const auto &scenario : w["scenarios"]) {
    auto sid = text(scenario, "id");
    auto mult = Rational::decimal(scenario.value("multiplier", "1"));
    int failed = integer(scenario, "failed_nodes", 0, 64);
    Rational total_read, total_write, total_network;
    bool resources_known = true, read_seen = false, write_seen = false, network_seen = false;
    for (const auto &s : w["stages"]) {
      auto id = text(s, "id"), type = text(s, "type");
      if (scenario.contains("active_stages") &&
          std::find(scenario["active_stages"].begin(), scenario["active_stages"].end(), id) ==
              scenario["active_stages"].end())
        continue;
      auto inputs = [&](std::initializer_list<const char *> fields) {
        Json a = Json::array();
        for (auto field : fields)
          if (s["observations"].contains(field))
            a.push_back(Json{{"path", "/stages/" + id + "/observations/" + field},
                             {"observation", s["observations"][field]}});
        a.push_back(Json{{"path", "/scenarios/" + sid}, {"scenario", scenario}});
        return a;
      };
      std::optional<Rational> rate;
      if (type == "inference" || type == "batch") {
        rate = q(s, "rate");
        if (!rate && q(s, "users") && q(s, "interval"))
          rate = *q(s, "users") / *q(s, "interval");
        if (type == "batch" && q(s, "jobs") && q(s, "window")) {
          rate = *q(s, "jobs") / *q(s, "window");
          out.add(id, sid, "reports_per_second", *rate, "request/s", "batch.volume_window",
                  inputs({"jobs", "window"}));
        }
        if (rate) {
          *rate = *rate * mult;
          out.add(id, sid, "transactions_per_second", *rate, "request/s", "demand.activity",
                  inputs({"rate", "users", "interval", "jobs", "window"}));
          for (auto field :
               {"extra_calls", "branch_probability", "fanout", "retry_probability", "max_retries"})
            if (s["observations"].contains(field) && !q(s, field)) {
              out.ask(id, field, "Unresolved expansion input prevents model-call rate resolution.");
              rate.reset();
            }
          for (auto pair : {std::pair{"retry_probability", "max_retries"},
                            std::pair{"branch_probability", "fanout"}})
            if (bool(q(s, pair.first)) != bool(q(s, pair.second))) {
              out.ask(id, pair.first,
                      "Both expansion parameters are required; partial description retained.");
              rate.reset();
            }
          if (type == "batch" && !q(s, "calls_per_job")) {
            out.ask(
                id, "calls_per_job",
                "Reports per second cannot establish model-call rate; supply calls per report.");
            rate.reset();
          }
          if (rate) {
            if (type == "batch")
              *rate = *rate * *q(s, "calls_per_job");
            *rate = *rate * (Rational(1) + q(s, "extra_calls").value_or(Rational(0)));
            if (q(s, "branch_probability") && q(s, "fanout"))
              *rate = *rate * *q(s, "branch_probability") * *q(s, "fanout");
            if (q(s, "retry_probability") && q(s, "max_retries")) {
              Rational attempts(1), term(1);
              for (int64_t n = 0; n < q(s, "max_retries")->num(); n++) {
                term = term * *q(s, "retry_probability");
                attempts = attempts + term;
              }
              *rate = *rate * attempts;
            }
            out.add(id, sid, "model_calls_per_second", *rate, "request/s", "demand.expansion",
                    inputs({"rate", "users", "interval", "jobs", "window", "extra_calls",
                            "calls_per_job", "branch_probability", "fanout", "retry_probability",
                            "max_retries"}));
            if (auto n = q(s, "input_tokens"))
              out.add(id, sid, "input_tokens_per_second", *rate * *n, "token/s", "demand.tokens",
                      inputs({"rate", "users", "interval", "jobs", "window", "extra_calls",
                              "calls_per_job", "branch_probability", "fanout", "retry_probability",
                              "max_retries", "input_tokens"}));
            if (auto n = q(s, "output_tokens"))
              out.add(id, sid, "output_tokens_per_second", *rate * *n, "token/s", "demand.tokens",
                      inputs({"rate", "users", "interval", "jobs", "window", "extra_calls",
                              "calls_per_job", "branch_probability", "fanout", "retry_probability",
                              "max_retries", "output_tokens"}));
          }
        } else
          out.ask(
              id, "observations",
              "Provide arrival rate or users and activity interval, or batch volume and window.");
      } else if (type == "training") {
        if (q(s, "tokens") && q(s, "window")) {
          auto time = *q(s, "window");
          out.add(id, sid, "calendar_tokens_per_second", *q(s, "tokens") / time, "token/s",
                  "training.calendar", inputs({"tokens", "window"}));
          if (auto effective = q(s, "effective_fraction"))
            time = time * *effective;
          if (auto overhead = q(s, "explicit_overhead")) {
            require(time > *overhead, "overhead", "Overhead exceeds deadline", id);
            time = time - *overhead;
          }
          bool overhead_known =
              q(s, "effective_fraction").has_value() || q(s, "explicit_overhead").has_value();
          if (!overhead_known)
            out.ask(id, "effective_fraction",
                    "Declare effective useful-time policy or explicit overhead; calendar rate is "
                    "only a lower bound.");
          for (auto field : {"effective_fraction", "explicit_overhead"})
            if (s["observations"].contains(field) && !q(s, field)) {
              overhead_known = false;
              out.ask(id, field, "Unresolved overhead prevents effective throughput resolution.");
            }
          if (overhead_known) {
            rate = *q(s, "tokens") * mult / time;
            out.add(id, sid, "effective_tokens_per_second", *rate, "token/s", "training.effective",
                    inputs({"tokens", "window", "effective_fraction", "explicit_overhead"}));
          }
        } else
          out.ask(id, "observations", "Training tokens and completion window are required.");
      } else if (type == "transfer") {
        if (q(s, "bytes") && q(s, "window")) {
          auto r = *q(s, "bytes") * mult / *q(s, "window");
          total_network = total_network + r;
          network_seen = true;
          out.add(id, sid, "payload_rate", r, "B/s", "transfer.window",
                  inputs({"bytes", "window"}));
          out.add(id, sid, "payload_Gbps", r / Rational(125000000), "Gbps", "units.bytes_to_bits",
                  inputs({"bytes", "window"}));
          if (q(s, "protocol_efficiency") && q(s, "utilization"))
            out.add(id, sid, "line_rate", r / *q(s, "protocol_efficiency") / *q(s, "utilization"),
                    "B/s", "network.line_rate",
                    inputs({"bytes", "window", "protocol_efficiency", "utilization"}));
          else
            out.ask(id, "observations",
                    "Line capacity requires protocol efficiency and utilization; latency needs "
                    "separate evidence.");
        } else {
          resources_known = false;
          out.ask(id, "observations", "Transfer bytes and window required.");
        }
      } else if (type == "data") {
        if (auto b = q(s, "bytes")) {
          auto free = q(s, "free_fraction");
          out.add(id, sid, "live_bytes", *b, "B", "storage.live", inputs({"bytes"}));
          if (free)
            out.add(id, sid, "usable_bytes", *b / (Rational(1) - *free), "B", "storage.free_space",
                    inputs({"bytes", "free_fraction"}));
          else
            out.ask(id, "free_fraction",
                    "Provide an explicit free-space policy to derive usable capacity.");
        } else
          resources_known = false;
      } else if (type == "checkpoint") {
        if (q(s, "checkpoint_bytes") && q(s, "save_window")) {
          auto r = *q(s, "checkpoint_bytes") / *q(s, "save_window");
          total_write = total_write + r;
          write_seen = true;
          out.add(id, sid, "durable_write_rate", r, "B/s", "checkpoint.write",
                  inputs({"checkpoint_bytes", "save_window"}));
          out.add(id, sid, "durable_write_GiBps", r / Rational(1073741824), "GiB/s",
                  "units.binary_rate", inputs({"checkpoint_bytes", "save_window"}));
        } else {
          resources_known = false;
          out.ask(id, "checkpoint_bytes", "Checkpoint representation and save window required.");
        }
        if (q(s, "checkpoint_bytes") && q(s, "recent") && q(s, "daily")) {
          auto count = *q(s, "recent") + *q(s, "daily");
          auto overlap = q(s, "retention_overlap");
          if (overlap) {
            require(*overlap <= *q(s, "recent") && *overlap <= *q(s, "daily"), "overlap",
                    "Overlap exceeds retained sets");
            count = count - *overlap;
          }
          out.add(id, sid, overlap ? "retained_bytes" : "retained_upper_bound_bytes",
                  count * *q(s, "checkpoint_bytes"), "B", "checkpoint.retention",
                  inputs({"recent", "daily", "retention_overlap", "checkpoint_bytes"}));
        }
      } else if (type == "cpu") {
        if (q(s, "rate") && q(s, "cpu_seconds") && q(s, "utilization"))
          out.add(id, sid, "cpu_cores",
                  Rational((*q(s, "rate") * *q(s, "cpu_seconds") / *q(s, "utilization")).ceil()),
                  "count", "host.cpu", inputs({"rate", "cpu_seconds", "utilization"}));
        else
          out.ask(id, "observations",
                  "CPU sizing requires measured core-seconds per operation, arrival rate and "
                  "utilization.");
      } else
        out.ask(id, "type", "No evaluator for this component.");
      if (auto r = q(s, "read_rate")) {
        total_read = total_read + *r;
        read_seen = true;
      } else if (type == "data")
        resources_known = false;
      if (auto r = q(s, "write_rate")) {
        total_write = total_write + *r;
        write_seen = true;
      } else if (type == "data")
        resources_known = false;
      if (rate) {
        bool matched = false;
        for (const auto &p : profiles) {
          if (p["kind"] != (type == "training" ? "training" : "inference"))
            continue;
          if (!s.contains("fingerprint") || s["fingerprint"] != p["fingerprint"])
            continue;
          if (s.contains("service_objectives") && !s["service_objectives"].empty() &&
              p["fingerprint"].value("service_objectives", Json::array()) !=
                  s["service_objectives"])
            continue;
          bool execution_matches = true;
          for (const auto field : {"model", "runtime", "precision"})
            if (s.contains(field) && s[field] != "unresolved" &&
                s[field] != p["fingerprint"].value(field, Json(nullptr)))
              execution_matches = false;
          if (!execution_matches)
            continue;
          if (s.contains("platforms") && std::find(s["platforms"].begin(), s["platforms"].end(),
                                                   p["platform"]) == s["platforms"].end())
            continue;
          matched = true;
          if (evaluated >= limit) {
            truncated = true;
            continue;
          }
          evaluated++;
          auto cap =
              Rational::decimal(text(p, "capacity")) * Rational::decimal(p.value("admission", "1"));
          int pernode = integer(p, "gpu_per_node", 0, 256),
              perrep = integer(p, "gpu_per_replica", 0, 256);
          Json constraints = Json::array();
          std::string status = "pass";
          auto check = [&](std::string name, std::string st, std::string message) {
            constraints.push_back(
                {{"name", name}, {"status", st}, {"message", message}, {"evidence", p["id"]}});
            if (st == "fail")
              status = "fail";
            else if (st == "unknown" && status != "fail")
              status = "unknown";
          };
          for (auto field : {"model", "runtime", "precision", "parallelism", "quality"})
            if (!p["fingerprint"].contains(field) || p["fingerprint"][field].is_null())
              check("execution_fingerprint", "unknown",
                    std::string("Missing applicability field: ") + field);
          if (type != "training") {
            for (auto pair : {std::pair{"input_tokens", "input_distribution"},
                              std::pair{"output_tokens", "output_distribution"}}) {
              auto shape = p["fingerprint"].value(pair.second, "");
              if (!q(s, pair.first) || !shape.starts_with("fixed-"))
                check("request_shape", "unknown",
                      "Only explicitly matched fixed request lengths are currently supported");
              else if (*q(s, pair.first) != Rational::decimal(shape.substr(6)))
                check("request_shape", "fail",
                      "Token observation differs from evidence fingerprint");
            }
            if (!p["fingerprint"].contains("slo") &&
                !p["fingerprint"].contains("service_objectives"))
              check("latency", "unknown", "Serving latency conditions are absent");
            if (!p["fingerprint"].contains("cache"))
              check("cache", "unknown", "Cache state missing");
            else if (scenario.contains("cache_state") &&
                     scenario["cache_state"] != p["fingerprint"]["cache"])
              check("cache", "fail", "Scenario cache state differs from evidence");
          } else {
            for (auto field : {"optimizer", "overhead_inclusion"})
              if (!p["fingerprint"].contains(field))
                check("training_execution", "unknown", std::string("Missing ") + field);
          }
          int64_t nodes = 0, gpus = 0;
          if (type == "training") {
            nodes = integer(p, "nodes", 0, 4096);
            gpus = nodes * pernode;
            check("deadline", cap >= *rate ? "pass" : "fail",
                  "Qualified throughput at exactly the measured node count");
            if (failed)
              check("recovery", "unknown",
                    "Training restart and surviving placement need recovery evidence");
          } else {
            if (perrep > pernode || pernode % perrep != 0) {
              check("placement", "unknown",
                    "Cross-node replicas require a separately implemented placement model");
            } else {
              auto healthy = (*rate / cap).ceil();
              nodes =
                  (Rational(Rational(healthy, pernode / perrep).ceil()) + Rational(failed)).num();
              gpus = (Rational(nodes) * Rational(pernode)).num();
              check("surviving_capacity",
                    Rational((nodes - failed) * (pernode / perrep)) * cap >= *rate ? "pass"
                                                                                   : "fail",
                    "Whole-node loss with independently placed replicas");
            }
          }
          if (p.contains("memory_required_bytes") && p.contains("hbm_bytes"))
            check("device_memory",
                  Rational::decimal(text(p, "memory_required_bytes")) <=
                          Rational::decimal(text(p, "hbm_bytes"))
                      ? "pass"
                      : "fail",
                  "Per-device total at exact execution fingerprint");
          else
            check("device_memory", "unknown", "Missing per-device memory evidence");
          if (w.value("tenancy", "single") == "multi" && !p.value("interference_qualified", false))
            check("tenancy", "unknown", "No matching tenant interference qualification");
          for (auto field : {"host_ram_bytes", "local_disk_bytes", "cpu_cores"})
            if (!p.contains(field))
              check(field, "unknown", "Host specification not qualified");
          require(gpus <= 9007199254740991LL && nodes <= 9007199254740991LL, "representation",
                  "Device count exceeds exact JSON integer profile");
          Json c = {{"id", id + ":" + sid + ":" + text(p, "id")},
                    {"stage_id", id},
                    {"scenario_id", sid},
                    {"platform", p["platform"]},
                    {"nodes", nodes},
                    {"gpus", gpus},
                    {"gpu_per_node", pernode},
                    {"profile_id", p["id"]},
                    {"status", status},
                    {"constraints", constraints},
                    {"evidence_channel", pack["channel"]},
                    {"host", Json::object()}};
          c["derivation"] = {{"rule", type == "training" ? "training.measured_configuration"
                                                         : "inference.whole_node_survival"},
                             {"version", "1.0"},
                             {"demand_rate", rate->exact()},
                             {"admitted_capacity", cap.exact()},
                             {"failed_nodes", failed},
                             {"profile_digest", digest(p)},
                             {"profile", p},
                             {"input_observations", s["observations"]},
                             {"scope", "Exact matched execution conditions only"}};
          c["memory"] = {
              {"per_device_required_bytes", p.value("memory_required_bytes", Json(nullptr))},
              {"per_device_hbm_bytes", p.value("hbm_bytes", Json(nullptr))},
              {"per_device_components_bytes", p.value("memory_components", Json::object())},
              {"missing_component_semantics", "Unspecified KV, workspace or host prefix-cache "
                                              "quantities remain unknown, not zero"},
              {"evidence_id", p["id"]}};
          for (auto k : {"host_ram_bytes", "local_disk_bytes", "cpu_cores"})
            if (p.contains(k))
              c["host"][k] = p[k];
          candidates.push_back(c);
        }
        if (!matched)
          out.ask(id, "fingerprint",
                  "No exact applicable serving or training evidence; GPU count unresolved.");
      }
    }
    if (read_seen)
      out.add("factory", sid, "declared_read_rate", total_read, "B/s", "flows.simultaneous",
              Json::array({"/scenarios/" + sid}));
    if (write_seen)
      out.add("factory", sid, "declared_write_rate", total_write, "B/s", "flows.simultaneous",
              Json::array({"/scenarios/" + sid}));
    if (network_seen)
      out.add("factory", sid, "declared_external_payload_rate", total_network, "B/s",
              "flows.directional", Json::array({"/scenarios/" + sid}));
    for (auto &c : candidates) {
      if (c["scenario_id"] != sid)
        continue;
      const auto &p = *std::find_if(profiles.begin(), profiles.end(),
                                    [&](const Json &x) { return x["id"] == c["profile_id"]; });
      for (const auto &[field, demand] :
           std::vector<std::pair<std::string, Rational>>{{"read_Bps", total_read},
                                                         {"write_Bps", total_write},
                                                         {"network_Bps", total_network}}) {
        std::string st = "unknown";
        if (resources_known && p.contains(field))
          st = Rational::decimal(text(p, field)) >= demand ? "pass" : "fail";
        c["constraints"].push_back(
            {{"name", field},
             {"status", st},
             {"message", "Qualified shared dependency capacity under this exact profile"},
             {"evidence", p["id"]}});
        if (st == "fail")
          c["status"] = "fail";
        else if (st == "unknown" && c["status"] != "fail")
          c["status"] = "unknown";
      }
    }
  }
  std::sort(candidates.begin(), candidates.end(), [](const Json &a, const Json &b) {
    return std::tuple(a["platform"].get<std::string>(), a["gpus"].get<int64_t>(),
                      a["id"].get<std::string>()) < std::tuple(b["platform"].get<std::string>(),
                                                               b["gpus"].get<int64_t>(),
                                                               b["id"].get<std::string>());
  });
  std::sort(out.questions.begin(), out.questions.end(),
            [](const Json &a, const Json &b) { return a["path"] < b["path"]; });
  out.questions.erase(std::unique(out.questions.begin(), out.questions.end()), out.questions.end());
  // Until portfolio placement is qualified, recommendations are explicitly per-stage/per-scenario
  // alternatives.
  int training_stages = 0, inference_stages = 0;
  for (const auto &stage : w["stages"]) {
    if (stage["type"] == "training")
      ++training_stages;
    if (stage["type"] == "inference" || stage["type"] == "batch")
      ++inference_stages;
  }
  Json characterization = {
      {"workload_character",
       training_stages ? (inference_stages ? "mixed_training_and_inference" : "training_centric")
                       : (inference_stages ? "inference_centric" : "non_gpu_or_unresolved")},
      {"training_stage_count", training_stages},
      {"inference_stage_count", inference_stages},
      {"training_share_percent", nullptr},
      {"inference_share_percent", nullptr},
      {"basis", "Declared stage families; percentage mix requires a common time horizon and "
                "utilization, not a ratio of incomparable token and transaction rates"}};
  auto resources = resolve_resources(w, pack);
  Json result = {
      {"schema_version", "1.0"},
      {"engine_version", engine_version},
      {"execution_profile", "rational64-v1"},
      {"engine_source_digest", ANUBIS_ENGINE_SHA256},
      {"workload_digest", digest(w)},
      {"knowledge_digest", digest(pack)},
      {"knowledge_channel", pack["channel"]},
      {"characterization", characterization},
      {"facts", out.facts},
      {"derivations", out.derivations},
      {"candidates", candidates},
      {"factory_configurations", resolve_factory(w, candidates)},
      {"resource_candidates", resources["candidates"]},
      {"resource_search", resources["search"]},
      {"questions", out.questions},
      {"search",
       {{"evaluated", evaluated},
        {"limit", limit},
        {"truncated", truncated},
        {"optimality", "not_claimed"}}},
      {"selection_state", "experimental"},
      {"scope",
       "per-stage and per-scenario; factory pooling and schedule qualification unresolved"},
      {"domains",
       {{"compute", candidates.empty() ? "unknown" : "conditional"},
        {"storage", "conditional"},
        {"network", "conditional"},
        {"tenancy", "unknown"}}}};
  add_planning(w, result);
  result["semantic_digest"] = digest(result);
  return result;
}
Json component_descriptors() {
  Json groups = {
      {"inference",
       {"users", "interval", "rate", "extra_calls", "input_tokens", "output_tokens",
        "branch_probability", "fanout", "retry_probability", "max_retries"}},
      {"batch", {"jobs", "window", "calls_per_job", "input_tokens", "output_tokens"}},
      {"training", {"tokens", "window", "effective_fraction", "explicit_overhead"}},
      {"transfer", {"bytes", "window", "protocol_efficiency", "utilization"}},
      {"data", {"bytes", "free_fraction", "read_rate", "write_rate"}},
      {"checkpoint", {"checkpoint_bytes", "save_window", "recent", "daily", "retention_overlap"}},
      {"cpu", {"rate", "cpu_seconds", "utilization", "host_bytes", "local_bytes"}}};
  const std::map<std::string, std::string> defaults = {
      {"count", "count"}, {"time", "s"},  {"rate", "request/s"}, {"token", "token"},
      {"ratio", "ratio"}, {"bytes", "B"}, {"byte_rate", "B/s"}};
  Json result = Json::object();
  for (auto it = groups.begin(); it != groups.end(); ++it) {
    result[it.key()] = Json::object();
    for (const auto &field : it.value())
      result[it.key()][field.get<std::string>()] = defaults.at(dimensions.at(field));
  }
  const std::set<std::string> data_fields = {
      "bytes", "free_fraction",     "read_rate",  "write_rate",  "checkpoint_bytes",   "recent",
      "daily", "retention_overlap", "host_bytes", "local_bytes", "protocol_efficiency"};
  Json phase_fields = {{"Demand", Json::object()}, {"Data", Json::object()}};
  for (auto it = result.begin(); it != result.end(); ++it) {
    phase_fields["Demand"][it.key()] = Json::object();
    phase_fields["Data"][it.key()] = Json::object();
    for (auto field = it.value().begin(); field != it.value().end(); ++field)
      phase_fields[data_fields.contains(field.key()) ? "Data" : "Demand"][it.key()][field.key()] =
          field.value();
  }
  return {{"version", "1.0"},
          {"fields", result},
          {"phase_fields", phase_fields},
          {"conditions", "registered_widgets_only"}};
}
Json capabilities() {
  return {
      {"engine_version", engine_version},
      {"normal_operation_requires_llm", false},
      {"coverage",
       {{"description", "partial"},
        {"modelling", "partial"},
        {"qualified_evidence", "none_bundled"}}},
      {"stage_types",
       {"inference", "batch", "training", "transfer", "data", "checkpoint", "cpu", "unsupported"}},
      {"phases",
       {"Purpose", "Composition", "Models", "Demand", "Service", "Data", "Operations", "Review"}},
      {"limits", {{"stages", 128}, {"scenarios", 32}, {"profiles", 256}, {"candidates", 4096}}},
      {"unsupported",
       {"cyclic graphs", "inferred probability distributions", "cross-node serving replicas",
        "global mixed-workload pooling", "remote downstream design tool project mutation",
        "shared production deployment"}}};
}
} // namespace anubis
