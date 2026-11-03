#pragma once
namespace anubis {
inline Json network_plan(const Json &w,const Json &plan) {
 auto n=w.value("characterization",Json::object()).value("guided_input",Json::object()).value("network",Json::object());
 keys(n,{"initial_tb","load_hours","daily_ingest_gb","daily_egress_gb","utilization","overlap","storage_read_gbps","storage_write_gbps","ew_per_gpu_gbps","latency_ms"},"network");
 auto get=[&](const char *k)->std::optional<Rational>{auto s=n.value(k,std::string(""));if(s.empty())return {};auto v=Rational::decimal(s);require(v>=Rational(0),"network",std::string(k)+" cannot be negative");return v;};
 auto json=[](const std::optional<Rational>&v)->Json{return v?Json(v->display(6)):Json(nullptr);};
 auto util=get("utilization").value_or(Rational(7,10));require(util>Rational(0)&&util<=Rational(1),"network","Usable link fraction must be above zero and at most one");
 auto overlap=n.value("overlap",std::string("yes"));require(overlap=="yes"||overlap=="no","network","Choose whether initial loading overlaps normal operation");
 auto volume=get("initial_tb"),hours=get("load_hours"),daily=get("daily_ingest_gb"),outdaily=get("daily_egress_gb");
 if(hours)require(*hours>Rational(0),"network","Initial load window must be positive");
 auto allowance=Rational::decimal(plan["policy"]["protocol_allowance"].get<std::string>());
 std::optional<Rational> initial;
 if(volume&&hours)initial=*volume*Rational(8000)/(*hours*Rational(3600))*allowance/util;
 auto appin=Rational::decimal(plan["ingress_Gbps"].get<std::string>()),appout=Rational::decimal(plan["egress_Gbps"].get<std::string>());
 auto steadyin=(appin+(daily?*daily*Rational(8,86400)*allowance:Rational(0)))/util;
 auto steadyout=(appout+(outdaily?*outdaily*Rational(8,86400)*allowance:Rational(0)))/util;
 std::optional<Rational> wanin;
 if(initial)wanin=overlap=="yes"?*initial+steadyin:std::max(*initial,steadyin);
 auto read=get("storage_read_gbps"),write=get("storage_write_gbps"),ew=get("ew_per_gpu_gbps"),latency=get("latency_ms");
 // Reuse declared storage measurements when the guided override is absent.
 auto stored=[&](const char *key)->std::optional<Rational>{Rational total;bool any=false;for(const auto &tier:plan["storage"]){if(tier[key].is_null())return {};any=true;total=total+Rational::decimal(tier[key].get<std::string>())*Rational(8,1000000000);}return any?std::optional<Rational>(total):std::nullopt;};
 if(!read)read=stored("read_Bps");if(!write)write=stored("write_Bps");
 if(write&&volume&&hours)write=std::max(*write,*volume*Rational(8000)/(*hours*Rational(3600)));
 Json missing=Json::array();
 for(const auto&s:w["stages"])if(s.contains("planning")&&s["planning"].contains("reference"))missing.push_back("Reference GPU capacity does not determine media, solver or training data traffic. Declare these payloads separately. Reported network rates remain lower bounds.");
 if(!initial)missing.push_back("Provide the initial customer-datacenter data volume and allowed transfer window.");
 if(!daily||!outdaily)missing.push_back("Ongoing bulk transfers are unspecified. Daily-volume rates are averages over 24 hours, not measured burst rates.");
 if(!read||!write)missing.push_back("Measure aggregate storage read and write throughput. Storage capacity alone does not determine fabric bandwidth.");
 if(!ew)missing.push_back("East-west per-GPU port demand needs the selected reference design and collective-communication measurements.");
 if(!latency)missing.push_back("Customer-datacenter round-trip latency objective is unspecified.");
 return {{"model_version","network-planning-1.0"},{"basis","Decimal TB and GB. Initial transfer rate = volume times 8 divided by transfer seconds. Apply protocol allowance and divide by usable link fraction. Application traffic is counted once at the external and north-south boundaries."},
 {"usable_link_fraction",util.display(3)},{"protocol_allowance",allowance.display(3)},{"initial_load_overlaps_operation",overlap=="yes"},
 {"external_customer_datacenter",{{"initial_load_link_Gbps",json(initial)},{"steady_ingress_lower_bound_Gbps",steadyin.display(6)},{"steady_egress_lower_bound_Gbps",steadyout.display(6)},{"required_ingress_lower_bound_Gbps",json(wanin)},{"round_trip_target_ms",json(latency)},{"status",initial?"conditional_lower_bound":"initial_load_unresolved"},{"connection","Customer datacenter to AI Factory routed connectivity. Carrier, redundancy and encryption design remain architect decisions."}}},
 {"north_south",{{"ingress_lower_bound_Gbps",json(wanin)},{"egress_lower_bound_Gbps",steadyout.display(6)},{"scope","Factory border to workload and storage endpoints. Carries the same external traffic, not an additional copy. Other tenants and non-model payloads need separate measurements."}}},
 {"storage",{{"dedicated",true},{"converged",false},{"technology","Ethernet"},{"read_payload_Gbps",json(read)},{"write_payload_Gbps",json(write)},{"read_link_lower_bound_Gbps",json(read?std::optional<Rational>(*read*allowance/util):std::nullopt)},{"write_link_lower_bound_Gbps",json(write?std::optional<Rational>(*write*allowance/util):std::nullopt)},{"scope","Physically dedicated storage fabric. Read and write are separate directions. Confirm bisection, fan-in, checkpoint bursts and initial-load writes. Unknown rates are not zero."}}},
 {"east_west",{{"fabric",plan["architecture"]["fabric"]},{"per_gpu_payload_Gbps",json(ew)},{"per_gpu_link_lower_bound_Gbps",json(ew?std::optional<Rational>(*ew*allowance/util):std::nullopt)},{"scope","GPU communication fabric. A fabric selection is not a qualified bandwidth or latency result."}}},{"follow_up",missing}};
}
}
