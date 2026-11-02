#include "compiler/resolution.hpp"
#include <map>
#include <set>
namespace anubis {
// Dedicated stage partitions are a conservative, deterministic placement policy.
// Neither statistical multiplexing nor cross-stage sharing is inferred.
Json resolve_factory(const Json &w, const Json &candidates) {
  std::set<std::string> platforms;
  for (const auto &c : candidates)
    platforms.insert(c["platform"]);
  Json configurations = Json::array();
  for (const auto &platform : platforms) {
    Json allocation = Json::array(), constraints = Json::array();
    int64_t total_nodes = 0, total_gpus = 0;
    std::string status = "pass";
    std::set<std::string> used_profiles;
    for (const auto &s : w["stages"]) {
      auto type = s["type"].get<std::string>(), id = s["id"].get<std::string>();
      if (type != "inference" && type != "batch" && type != "training")
        continue;
      int64_t maxnodes = 0, maxgpus = 0;
      Json members = Json::array();
      for (const auto &sc : w["scenarios"]) {
        if (sc.contains("active_stages") &&
            std::find(sc["active_stages"].begin(), sc["active_stages"].end(), id) ==
                sc["active_stages"].end())
          continue;
        std::vector<Json> options;
        for (const auto &c : candidates)
          if (c["platform"] == platform && c["stage_id"] == id && c["scenario_id"] == sc["id"] &&
              c["status"] != "fail" && c["gpus"].get<int64_t>() > 0)
            options.push_back(c);
        std::sort(options.begin(), options.end(), [](const Json &a, const Json &b) {
          return std::tuple(a["status"] != "pass", a["gpus"].get<int64_t>(),
                            a["id"].get<std::string>()) < std::tuple(b["status"] != "pass",
                                                                     b["gpus"].get<int64_t>(),
                                                                     b["id"].get<std::string>());
        });
        if (options.empty()) {
          status = "unknown";
          constraints.push_back(
              {{"stage_id", id},
               {"scenario_id", sc["id"]},
               {"status", "unknown"},
               {"reason",
                "No nonfailed applicable placement; absence does not establish infeasibility"}});
          continue;
        }
        auto c = options.front();
        if (c["status"] != "pass")
          status = "unknown";
        maxnodes = std::max(maxnodes, c["nodes"].get<int64_t>());
        maxgpus = std::max(maxgpus, c["gpus"].get<int64_t>());
        used_profiles.insert(c["profile_id"]);
        members.push_back(c["id"]);
      }
      total_nodes += maxnodes;
      total_gpus += maxgpus;
      allocation.push_back({{"stage_id", id},
                            {"reserved_nodes", maxnodes},
                            {"reserved_gpus", maxgpus},
                            {"scenario_candidates", members}});
    }
    // Per-profile IO measurements do not qualify a multi-profile shared fabric.
    if (used_profiles.size() > 1) {
      status = "unknown";
      constraints.push_back({{"status", "unknown"},
                             {"reason", "Combined workload requires joint shared-storage/fabric "
                                        "and execution-interference evidence"}});
    }
    require(total_gpus <= 9007199254740991LL && total_nodes <= 9007199254740991LL, "representation",
            "Factory reservation exceeds exact JSON integer profile");
    configurations.push_back(
        {{"id", "factory:" + platform},
         {"platform", platform},
         {"nodes", total_nodes},
         {"gpus", total_gpus},
         {"status", status},
         {"allocation", allocation},
         {"constraints", constraints},
         {"policy", "dedicated_stage_partitions; maximum reservation across declared scenarios"},
         {"optimality", "not_claimed"},
         {"scope",
          "compute reservation envelope; infrastructure domains require separate evidence"}});
  }
  return configurations;
}
} // namespace anubis
