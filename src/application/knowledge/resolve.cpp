#include "application/knowledge/resolve.hpp"
#include <map>
#include <set>
namespace anubis {
Json resolve_knowledge(const std::string &root,
                       const std::function<Json(const std::string &)> &fetch) {
  std::set<std::string> visiting, done;
  std::map<std::string, Json> profiles, sources, resources;
  Json locks = Json::array();
  bool synthetic = false;
  std::function<void(const std::string &)> visit = [&](const std::string &hash) {
    require(!visiting.contains(hash), "dependency_cycle", "Knowledge dependency cycle");
    if (done.contains(hash))
      return;
    require(done.size() + visiting.size() < 64, "dependency_limit", "At most 64 packs per lock");
    visiting.insert(hash);
    auto pack = fetch(hash);
    require(digest(pack) == hash, "digest_mismatch",
            "Knowledge content does not match dependency digest");
    validate_pack(pack);
    auto deps = pack.value("dependencies", Json::array());
    std::sort(deps.begin(), deps.end());
    for (const auto &dep : deps)
      visit(dep.get<std::string>());
    synthetic |= pack["channel"] == "synthetic";
    for (auto profile : pack["profiles"]) {
      auto id = text(profile, "id");
      require(!profiles.contains(id) || profiles[id] == profile, "knowledge_conflict",
              "Conflicting evidence with equal identity; create a new evidence ID", id);
      profiles[id] = profile;
    }
    for (auto resource : pack.value("resource_profiles", Json::array())) {
      auto id = text(resource, "id");
      require(!resources.contains(id) || resources[id] == resource, "knowledge_conflict",
              "Conflicting resource evidence identity", id);
      resources[id] = resource;
    }
    for (auto source : pack.value("sources", Json::array())) {
      auto id = text(source, "id");
      require(!sources.contains(id) || sources[id] == source, "source_conflict",
              "Conflicting source identity", id);
      sources[id] = source;
    }
    locks.push_back({{"id", pack["id"]}, {"version", pack["version"]}, {"sha256", hash}});
    visiting.erase(hash);
    done.insert(hash);
  };
  visit(root);
  Json resolved = {{"schema_version", "1.0"},
                   {"id", "resolved:" + root},
                   {"version", "1"},
                   {"channel", synthetic ? "synthetic" : "qualified"},
                   {"profiles", Json::array()},
                   {"sources", Json::array()}};
  for (const auto &[id, p] : profiles)
    resolved["profiles"].push_back(p);
  for (const auto &[id, s] : sources)
    resolved["sources"].push_back(s);
  resolved["resource_profiles"] = Json::array();
  for (const auto &[id, r] : resources)
    resolved["resource_profiles"].push_back(r);
  validate_pack(resolved);
  std::sort(locks.begin(), locks.end(),
            [](const Json &a, const Json &b) { return a["sha256"] < b["sha256"]; });
  return {{"root_digest", root},
          {"entries", locks},
          {"resolved", resolved},
          {"resolved_digest", digest(resolved)},
          {"resolver_version", "1.0"}};
}
} // namespace anubis
