#include "application/intake/import.hpp"
#include <set>
namespace anubis {
Json preview_import(const Json &workload, const Json &rows) {
  require(rows.is_array() && rows.size() <= 2000, "import_limit",
          "Supply at most 2000 typed observation rows");
  auto proposed = workload;
  Json accepted = Json::array(), rejected = Json::array();
  std::set<std::pair<std::string, std::string>> touched;
  for (size_t i = 0; i < rows.size(); ++i) {
    try {
      const auto &row = rows[i];
      keys(row, {"stage_id", "field", "observation"}, "/rows");
      auto stage = text(row, "stage_id"), field = text(row, "field");
      require(touched.insert({stage, field}).second, "duplicate_row",
              "Observation repeated in import");
      auto candidate = proposed;
      auto it = std::find_if(candidate["stages"].begin(), candidate["stages"].end(),
                             [&](const Json &s) { return s["id"] == stage; });
      require(it != candidate["stages"].end(), "stage_reference", "Unknown stage", stage);
      (*it)["observations"][field] = row.at("observation");
      validate_workload(candidate);
      proposed = candidate;
      accepted.push_back({{"row", i + 1}, {"input", row}});
    } catch (const Error &e) {
      rejected.push_back({{"row", i + 1}, {"input", rows[i]}, {"error", error_json(e)["error"]}});
    } catch (const Json::exception &) {
      rejected.push_back({{"row", i + 1},
                          {"input", rows[i]},
                          {"error", {{"code", "contract"}, {"message", "Malformed row"}}}});
    }
  }
  return {{"accepted", accepted},
          {"rejected", rejected},
          {"proposed_workload", proposed},
          {"source_digest", digest(rows)},
          {"preview_digest", digest(proposed)}};
}
} // namespace anubis
