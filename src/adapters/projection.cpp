#include "compiler/compiler.hpp"
#include <algorithm>
namespace anubis {
Json project(const Json &result, const Json &r) {
  keys(r,
       {"candidate_id", "platform", "network_fabric", "storage_fabric", "project_name",
        "accept_substitution", "storage_fact_id", "storage_model", "tenancy_model"},
       "/projection");
  auto id = text(r, "candidate_id");
  auto it = std::find_if(result["candidates"].begin(), result["candidates"].end(),
                         [&](const Json &c) { return c["id"] == id; });
  require(it != result["candidates"].end(), "candidate", "Select an existing candidate");
  const auto &c = *it;
  require(c["status"] != "fail", "infeasible", "Cannot project a failed candidate");
  auto platform = text(r, "platform");
  require(platform == "HGX_B300" || platform == "GB300_NVL72", "platform",
          "Target profile allows HGX_B300 or GB300_NVL72");
  bool substitute = c["platform"] != platform;
  require(!substitute || r.value("accept_substitution", false), "decision_required",
          "Explicit substitution acceptance required");
  auto fabric = text(r, "network_fabric");
  require(fabric == "InfiniBand" || fabric == "Spectrum-X", "fabric", "Unsupported target fabric");
  require(c["gpus"].get<int64_t>() > 0, "gpu_count", "Candidate has no resolved GPU count");
  bool planning=c.value("planning",false);
  if(planning) {
    const auto &p=result.at("planning");
    require(p["status"]=="conditional", "planning_status", "Resolve planning feasibility before handoff");
    require(!substitute && p["architecture"]["fabric"]==fabric, "planning_profile", "Recompile using the selected platform/fabric profile before handoff; anchor sets differ");
  }
  Json payload = {{"project", {{"name", r.value("project_name", "Anubis scenario")}}},
                  {"requirements",
                   {{"platform", platform},
                    {"target_gpu_count", c["gpus"]},
                    {"network_fabric", fabric},
                    {"east_west_fabric", fabric}}}};
  if (r.contains("storage_fabric")) {
    auto f = text(r, "storage_fabric");
    require(f == "InfiniBand" || f == "Spectrum-X_Ethernet" || f == "Ethernet", "storage_fabric",
            "Unsupported enum");
    payload["requirements"]["storage_fabric"] = f;
  }
  if (r.contains("tenancy_model")) {
    auto t = text(r, "tenancy_model");
    require(t == "single_tenant" || t == "multi_tenant", "tenancy", "Unsupported target tenancy");
    payload["requirements"]["tenancy_model"] = t;
  }
  Json ledger = Json::array(
      {{{"field", "requirements.platform"},
        {"intended", c["platform"]},
        {"projected", platform},
        {"mode", substitute ? "substitution" : "direct"},
        {"affected_domains",
         {"physical_compute", "node_count", "NIC_endpoints", "scale_up", "failure_domains"}},
        {"assessment", "external_adjustment"}},
       {{"field", "requirements.target_gpu_count"},
        {"intended", c["gpus"]},
        {"projected", c["gpus"]},
        {"rounding", "downstream design tool result requires reassessment"}}});
  if (r.contains("storage_fact_id")) {
    auto fid = text(r, "storage_fact_id");
    auto f = std::find_if(result["facts"].begin(), result["facts"].end(),
                          [&](const Json &x) { return x["id"] == fid; });
    require(f != result["facts"].end() && (*f)["name"] == "usable_bytes", "storage_scope",
            "Choose exactly one derived usable storage tier");
    auto b = Rational(std::stoll((*f)["exact"]["numerator"].get<std::string>()),
                      std::stoll((*f)["exact"]["denominator"].get<std::string>()));
    require(b.den() == 1 && b.num() <= 9007199254740991LL, "representation",
            "Storage bytes not safely representable by target JSON number");
    auto tib = b / Rational(1099511627776LL);
    auto rounded = Rational((tib * Rational(1000000)).ceil(), 1000000);
    payload["requirements"]["storage_capacity"] = {
        {"usable", {{"value", std::stod(rounded.display(6))}, {"unit", "TiB"}}}};
    ledger.push_back({{"field", "requirements.storage_capacity.usable"},
                      {"fact_id", fid},
                      {"tier_scope", (*f)["stage_id"]},
                      {"omission", "Other storage tiers remain external"},
                      {"reserve", "Already included upstream; downstream reserve unresolved"},
                      {"rounding", "Upward to 0.000001 TiB for target numeric field"}});
  }
  Json brief=Json::object();
  if(planning) {
    const auto &p=result.at("planning"); brief=p;
    payload["requirements"]["tenancy_model"]=p["tenancy"]=="multi"?"multi_tenant":"single_tenant";
    payload["requirements"]["storage_fabric"]="Ethernet";
    bool mapped=false;
    for(const auto &tier:p["storage"]) {
      auto t=tier["tier"].get<std::string>();
      if(!mapped && (t=="file"||t=="parallel_file")&&tier["capacity_known"]==true) {
        payload["requirements"]["storage_model"]="HPS";
        payload["requirements"]["storage_capacity"]={{"usable",{{"value",std::stod(tier["usable_bytes"].get<std::string>())/1099511627776.0},{"unit","TiB"}}}};
        mapped=true;
        ledger.push_back({{"field","requirements.storage_capacity.usable"},{"stage_id",tier["stage_id"]},{"mode","direct"},{"reserve","Included upstream; verify downstream sizing"}});
      } else ledger.push_back({{"field","storage tier"},{"stage_id",tier["stage_id"]},{"mode","brief_only"},{"reason","Existing single HPS tier must not collapse object and file requirements"}});
    }
    ledger.push_back({{"field","north_south"},{"mode","brief_only"},{"reason","No verified intake field. Architect must apply ingress and egress requirements."}});
    ledger.push_back({{"field","external_customer_datacenter"},{"mode","brief_only"},{"reason","Initial loading, ongoing link rates and latency targets require architect action."}});
    ledger.push_back({{"field","dedicated_storage_network"},{"mode","brief_only"},{"reason","Intake carries Ethernet technology only. Physical separation, no convergence and bandwidth require architect action."}});
    ledger.push_back({{"field","N-S ingress/egress, per-device VRAM, host RAM, CPU, local disk and tier throughput"},{"mode","brief_only"},{"reason","No verified equivalent intake scalar; retain in companion specification"}});
  }
  std::string worksheet="downstream design tool intake\n"+payload.dump(2)+"\n\nMapping and external requirements\n"+ledger.dump(2);
  if(planning) {
    const auto &p=result.at("planning");
    worksheet="Anubis planning architecture brief\nInitial GPUs: "+p["initial_gpus"].dump()+"\nRaw workload GPUs: "+p["raw_gpus"].dump()+"\nPlatform: "+platform+"\nFabric: "+fabric+"\nVRAM required per GPU (GB): "+p["required_GB_per_gpu"].get<std::string>()+"\nHost RAM required (GB): "+p["host_ram_GB_required"].get<std::string>()+"\nDeclared traffic before link-utilization allowance (Gbps): "+p["ingress_Gbps"].get<std::string>()+" / "+p["egress_Gbps"].get<std::string>()+"\nNetwork requirements: "+p.value("networks",Json::object()).dump(2)+"\nStorage policy: Physically dedicated storage network. No converged network.\nStorage tiers: "+p["storage"].dump(2)+"\nAssumptions: "+p["policy"].dump(2)+"\nAnalytical planning, not a performance guarantee.\n\n"+worksheet;
    if(p.contains("workload_capacity"))worksheet+="\nEquivalent workload capacity\n"+p["workload_capacity"].dump(2)+"\n";
  }
  return {{"worksheet",worksheet},{"companion_requirements",brief}, {"target_profile", "neon-source-01bccd6-manual-v1"},
          {"target_qualified_live", false},
          {"payload", payload},
          {"payload_digest", digest(payload)},
          {"intended_configuration", c},
          {"mapping_ledger", ledger},
          {"projection_mode", substitute ? "substitution" : "partial"},
          {"external_obligations",
           {"Verify modelling node count and NIC endpoints",
            "Preserve host and physical compute specification",
            "Qualify separate storage tiers and reserve handling",
            "Assess returned fabrics and capacity"}},
          {"selection_state", "experimental"}};
}
Json assess(const Json &projection, const Json &external) {
  Json a = Json::array();
  for (auto domain : {"compute", "storage", "network", "tenancy", "connectivity"})
    a.push_back({{"domain", domain},
                 {"status", "unverifiable"},
                 {"reason", "Imported architecture retained; no target-qualified domain evidence "
                            "adapter is activated"}});
  Json reconciliation = Json::array();
  if (external.contains("architecture_model") && external["architecture_model"].contains("scale")) {
    const auto &scale = external["architecture_model"]["scale"];
    if (scale.contains("actual_gpu_count") && scale["actual_gpu_count"].is_number_integer())
      reconciliation.push_back(
          {{"field", "/architecture_model/scale/actual_gpu_count"},
           {"requested", projection["payload"]["requirements"]["target_gpu_count"]},
           {"returned", scale["actual_gpu_count"]},
           {"status",
            scale["actual_gpu_count"] == projection["payload"]["requirements"]["target_gpu_count"]
                ? "value_matches"
                : "external_adjustment"},
           {"meaning", "Field reconciliation only; not workload feasibility verification"}});
  }
  if(external.contains("selected_architecture") && external["selected_architecture"].contains("platform")) {
    const auto actual=external["selected_architecture"]["platform"];
    const auto requested=projection["payload"]["requirements"]["platform"];
    reconciliation.push_back({{"field","/selected_architecture/platform"},{"requested",requested},{"returned",actual},{"status",actual==requested?"value_matches":"external_adjustment"},{"meaning","Platform reconciliation; does not establish workload feasibility"}});
  }
  Json authority = Json::object();
  for (auto key :
       {"authority", "governance", "architecture_readiness", "result_status", "diagnostics"})
    if (external.contains(key))
      authority[key] = external[key];
  return {{"projection_digest", digest(projection)},
          {"external_digest", digest(external)},
          {"external_authority", authority},
          {"field_reconciliation", reconciliation},
          {"domains", a},
          {"selection_state", "experimental"}};
}
} // namespace anubis
