#include "compiler/qualification.hpp"
#include <set>
namespace anubis {
Json validate_protocol(const Json &p) {
  keys(p,
       {"pack_digest", "metric", "measurement_boundary", "quality_conditions", "min_cases",
        "max_relative_error", "max_false_feasible_fraction", "calibration_configuration_ids",
        "domain", "source"},
       "/protocol");
  require(text(p, "pack_digest").size() == 64, "digest", "SHA256 pack digest required");
  for (auto k : {"metric", "measurement_boundary", "quality_conditions", "domain", "source"})
    require(!text(p, k).empty(), "required", "Protocol field required", k);
  require(p.contains("min_cases") && p["min_cases"].is_number_integer() &&
              p["min_cases"].get<int>() >= 2 && p["min_cases"].get<int>() <= 10000,
          "min_cases", "Declare 2 to 10000 held-out cases");
  for (auto k : {"max_relative_error", "max_false_feasible_fraction"}) {
    auto r = Rational::decimal(text(p, k));
    require(r >= Rational(0) && r <= Rational(1), "tolerance", "Tolerance must be in [0,1]", k);
  }
  require(p.contains("calibration_configuration_ids") &&
              p["calibration_configuration_ids"].is_array(),
          "calibration", "Calibration split must be declared");
  return {{"valid", true}, {"protocol_digest", digest(p)}};
}
Json evaluate_qualification(const Json &protocol, const Json &dataset) {
  validate_protocol(protocol);
  keys(dataset, {"protocol_digest", "source_artifact_sha256", "source", "cases"}, "/dataset");
  require(text(dataset, "protocol_digest") == digest(protocol), "protocol_mismatch",
          "Dataset must reference the predeclared protocol");
  require(text(dataset, "source_artifact_sha256").size() == 64, "artifact",
          "Measurement artifact SHA256 required");
  text(dataset, "source");
  const auto &cases = dataset.at("cases");
  require(cases.is_array() && cases.size() >= protocol["min_cases"].get<size_t>() &&
              cases.size() <= 10000,
          "sample_count", "Held-out sample count outside declared range");
  std::set<std::string> used;
  Rational worst, errors;
  int64_t false_feasible = 0;
  Json rows = Json::array();
  for (const auto &c : cases) {
    keys(c, {"configuration_id", "predicted", "measured", "predicted_pass", "observed_pass"},
         "/cases");
    auto id = text(c, "configuration_id");
    require(used.insert(id).second, "duplicate_case", "Configuration repeated in held-out set");
    for (const auto &prior : protocol["calibration_configuration_ids"])
      require(prior != id, "data_leakage", "Held-out configuration appears in calibration set");
    auto pred = Rational::decimal(text(c, "predicted")),
         measured = Rational::decimal(text(c, "measured"));
    require(pred >= Rational(0) && measured > Rational(0), "measurement",
            "Positive measurement and nonnegative prediction required");
    auto error = (pred >= measured ? pred - measured : measured - pred) / measured;
    errors = errors + error;
    if (error > worst)
      worst = error;
    require(c.contains("predicted_pass") && c["predicted_pass"].is_boolean() &&
                c.contains("observed_pass") && c["observed_pass"].is_boolean(),
            "classification", "Both feasibility classifications required");
    if (c["predicted_pass"].get<bool>() && !c["observed_pass"].get<bool>())
      false_feasible++;
    rows.push_back({{"configuration_id", id}, {"relative_error", error.exact()}});
  }
  auto false_rate = Rational(false_feasible, static_cast<int64_t>(cases.size()));
  bool pass = worst <= Rational::decimal(text(protocol, "max_relative_error")) &&
              false_rate <= Rational::decimal(text(protocol, "max_false_feasible_fraction"));
  return {{"pass", pass},
          {"scope", protocol["domain"]},
          {"protocol_digest", digest(protocol)},
          {"dataset_digest", digest(dataset)},
          {"pack_digest", protocol["pack_digest"]},
          {"case_count", cases.size()},
          {"worst_relative_error", worst.exact()},
          {"mean_relative_error", (errors / Rational(static_cast<int64_t>(cases.size()))).exact()},
          {"false_feasible_fraction", false_rate.exact()},
          {"cases", rows},
          {"requires_independent_approval", true}};
}

} // namespace anubis
