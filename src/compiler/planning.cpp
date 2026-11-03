#include "compiler/planning.hpp"
#include <algorithm>
#include "compiler/network_plan.hpp"
namespace anubis {
Json planning_catalog() { return parse(
#include "compiler/planning_catalog.inc"
); }
static Rational number(const Json &j, const char *k, const char *fallback="") {
  auto s=j.value(k,std::string(fallback));
  require(!s.empty(),"planning_input",std::string("Supply planning input: ")+k);
  auto v=Rational::decimal(s); require(v>=Rational(0),"planning_input","Negative planning input");return v;
}
static int count(const Json &j,const char *k) {
 require(j.contains(k)&&j[k].is_number_integer(),"planning_input",std::string("Integer required: ")+k);
 auto n=j[k].get<int64_t>();require(n>0&&n<=1000000,"planning_input","Planning count outside 1..1000000");return static_cast<int>(n);
}
void validate_planning(const Json &w) {
 if(!w.contains("planning"))return;
 auto p=w["planning"];
 keys(p,{"architecture","sensitivity_percent","compute_efficiency","memory_efficiency","minimum_service_fraction","accept_capacity_shortfall","bytes_per_token","protocol_allowance","assumptions_accepted","expansion_lead_days","source"},"/planning");
 for(auto k:{"compute_efficiency","memory_efficiency","minimum_service_fraction"}) {auto v=number(p,k);require(v>Rational(0)&&v<=Rational(1),"planning_fraction","Planning fraction must be in (0,1]");}
 auto band=number(p,"sensitivity_percent");require(band>=Rational(10)&&band<=Rational(80),"planning_band","Sensitivity must be 10..80 percent");
 require(number(p,"bytes_per_token")>Rational(0)&&number(p,"protocol_allowance")>=Rational(1),"planning_network","Positive bytes/token and protocol allowance >=1 required");
 count(p,"expansion_lead_days");text(p,"source");
 for(auto k:{"assumptions_accepted","accept_capacity_shortfall"})require(p.contains(k)&&p[k].is_boolean(),"planning_input","Acceptance must be boolean");
 for(const auto &s:w["stages"])if(s.contains("planning")) {
  auto a=s["planning"];
  keys(a,{"model","parallel_gpus","concurrent_sequences","context_tokens","weight_bytes","kv_bytes","workspace_GB","training_bytes_per_parameter","activation_GB_per_gpu","host_ram_GB_per_gpu","local_disk_GB_per_gpu","cpu_cores_per_gpu","reference"},"/stages/planning");
  if(a.contains("reference")) {
   const auto &ref=a["reference"];keys(ref,{"demand","unit","group_gpus","memory_GB","capacities","source","accepted","independent_groups"},"/reference");
   for(auto k:{"demand","group_gpus","memory_GB"})require(number(ref,k)>Rational(0),"reference","Positive reference quantities required");
   auto group=number(ref,"group_gpus");require(group==Rational(group.ceil())&&group<=Rational(1024)&&(group.ceil()<8?8%group.ceil()==0:group.ceil()%8==0),"reference","Reference groups must use 1, 2, 4, 8 or a multiple of 8 GPUs, up to 1024");
   require(!text(ref,"source").empty()&&!text(ref,"unit").empty()&&ref.value("accepted",false)&&ref.value("independent_groups",false),"reference","Accept scoped independent reference groups and identify the source and work unit");
   keys(ref["capacities"],{"HGX_H200","HGX_B200","HGX_B300"},"/reference/capacities");
   for(auto k:{"HGX_H200","HGX_B200","HGX_B300"})require(number(ref["capacities"],k)>Rational(0),"reference","Each GPU platform needs its own positive capacity");
   count(a,"cpu_cores_per_gpu");number(a,"host_ram_GB_per_gpu");number(a,"local_disk_GB_per_gpu");continue;
  }
  for(auto k:{"parallel_gpus","concurrent_sequences","context_tokens","cpu_cores_per_gpu"})count(a,k);
  for(auto k:{"weight_bytes","kv_bytes","workspace_GB","training_bytes_per_parameter","activation_GB_per_gpu","host_ram_GB_per_gpu","local_disk_GB_per_gpu"})number(a,k);
  require(number(a,"weight_bytes")>Rational(0)&&number(a,"kv_bytes")>Rational(0)&&number(a,"training_bytes_per_parameter")>=number(a,"weight_bytes"),"planning_memory","Invalid memory precision/state assumptions");
 }
}
static std::optional<Rational> fact(const Json &r,const std::string &stage,const std::string &scenario,const std::string &name) {
 for(const auto &f:r["facts"])if(f["stage_id"]==stage&&f["scenario_id"]==scenario&&f["name"]==name)return Rational(std::stoll(f["exact"]["numerator"].get<std::string>()),std::stoll(f["exact"]["denominator"].get<std::string>()));
 return {};
}
static void add_planning_impl(const Json &w,Json &r,const std::string &comparison_platform="") {
 if(!w.contains("planning"))return;
 validate_planning(w);auto p=w["planning"];auto cat=planning_catalog();
 auto ai=std::find_if(cat["architectures"].begin(),cat["architectures"].end(),[&](const Json &a){return a["id"]==p["architecture"];});
 require(ai!=cat["architectures"].end(),"architecture","Choose an available architecture profile");
 auto architecture=*ai;auto platform=architecture["platform"].get<std::string>();auto hw=cat["hardware"][comparison_platform.empty()?platform:comparison_platform];
 const auto gpn=hw["gpu_per_node"].get<int>();auto hbm=number(hw,"hbm_GB");auto usable=hbm*number(hw,"usable_hbm_fraction");
 auto efficiency=number(p,"compute_efficiency"), me=number(p,"memory_efficiency");
 auto tf=number(hw,"dense_bf16_TFLOPS")*efficiency;
 auto bandwidth=number(hw,"bandwidth_TBps")*Rational(1000)*me;
 auto band=number(p,"sensitivity_percent")/Rational(100);
 Json stages=Json::array(), scenarios=Json::array(),gaps=Json::array(),storage=Json::array();
 int64_t nominal=0,downside=0,upside=0,memory_floor=0;Rational ingress,egress,host,local,cores,maxmemory;
 bool failed=false;int gpu_stages=0;
 for(const auto &sc:w["scenarios"]) {
  auto sid=sc["id"].get<std::string>();int64_t total=0,lower=0,upper=0,floor=0;Rational in,out,sh,sl,cp;
  for(const auto &s:w["stages"]) {
   auto id=s["id"].get<std::string>();auto type=s["type"].get<std::string>();
   if(sc.contains("active_stages")&&std::find(sc["active_stages"].begin(),sc["active_stages"].end(),id)==sc["active_stages"].end())continue;
   if(s.contains("planning")&&s["planning"].contains("reference")) {
    gpu_stages++;auto a=s["planning"];auto ref=a["reference"];auto key=comparison_platform.empty()?platform:comparison_platform;
    if(!ref["capacities"].contains(key)){gaps.push_back(id+": no reference capacity for selected GPU platform");continue;}
    auto demand=number(ref,"demand")*Rational::decimal(sc.value("multiplier",std::string("1"))),capacity=number(ref["capacities"],key.c_str()),group=number(ref,"group_gpus"),required=number(ref,"memory_GB");
    auto allocation=[&](Rational cap){return (Rational((demand/cap).ceil())*group/Rational(gpn)).ceil()*gpn;};
    auto g=allocation(capacity),lo=allocation(capacity*(Rational(1)+band)),hi=allocation(capacity*(Rational(1)-band));
    total+=g;lower+=lo;upper+=hi;floor+=(group/Rational(gpn)).ceil()*gpn;
    maxmemory=std::max(maxmemory,required);bool fits=required<=usable;failed=failed||!fits;
    sh=sh+Rational(g)*number(a,"host_ram_GB_per_gpu");sl=sl+Rational(g)*number(a,"local_disk_GB_per_gpu");cp=cp+Rational(g)*Rational(count(a,"cpu_cores_per_gpu"));
    stages.push_back({{"stage_id",id},{"scenario_id",sid},{"model",{{"name","Reference workload"}}},{"assumptions",a},{"reference",ref},{"raw_gpus",g},{"replicas",(demand/capacity).ceil()},{"capacity_per_replica",capacity.display(6)},{"capacity_unit",text(ref,"unit")+"/s per reference group"},{"demand_unit",text(ref,"unit")+"/s"},{"demand",demand.display(6)},{"required_GB_per_gpu",required.display(6)},{"memory_fit",fits},{"rule","ceil(demand / capacity per independent group) × group GPUs, rounded to whole nodes. No cross-hardware or single-job scaling inferred."}});
    continue;
   }
   if(type=="unsupported" && w.value("characterization",Json::object()).contains("guided_input")) gaps.push_back(id+": specialist component not included in GPU subtotal");
   if(type=="transfer")in=in+fact(r,id,sid,"payload_rate").value_or(Rational(0));
   if(type!="training"&&type!="inference"&&type!="batch")continue;
   gpu_stages++;
   if(!s.contains("planning")){gaps.push_back(id+": model and sizing assumptions required");continue;}
   auto a=s["planning"];auto mid=text(a,"model");
   require(cat["models"].contains(mid),"planning_model","Select a supported planning model");auto model=cat["models"][mid];
   auto params=number(model,"parameters");int parallel=count(a,"parallel_gpus");
   if(parallel>gpn||gpn%parallel!=0){gaps.push_back(id+": this planning release requires replicas within one node/tray");continue;}
   auto rate=fact(r,id,sid,type=="training"?"effective_tokens_per_second":"model_calls_per_second");
   if(!rate){gaps.push_back(id+": demand remains unresolved");continue;}
   Rational kv,weights=params/Rational(1000000000)*number(a,"weight_bytes"),required,capacity,ins,outs;
   if(type=="training") {
    required=params/Rational(1000000000)*number(a,"training_bytes_per_parameter")/Rational(parallel)+number(a,"activation_GB_per_gpu")+number(a,"workspace_GB");
    capacity=tf*Rational(1000000000000LL)*Rational(parallel)/(Rational(6)*params);
   } else {
    auto it=fact(r,id,sid,"input_tokens_per_second"),ot=fact(r,id,sid,"output_tokens_per_second");
    if(!it||!ot||*rate==Rational(0)){gaps.push_back(id+": positive rate and input/output tokens required");continue;}
    ins=*it/ *rate;outs=*ot/ *rate;
    require(Rational(count(a,"context_tokens"))>=ins+outs,"context","Context allocation must cover input and output tokens");
    kv=Rational(2)*Rational(model["layers"].get<int>())*Rational(model["kv_heads"].get<int>())*Rational(model["head_dimension"].get<int>())*number(a,"kv_bytes")*Rational(count(a,"context_tokens"))*Rational(count(a,"concurrent_sequences"))/Rational(1000000000);
    required=(weights+kv)/Rational(parallel)+number(a,"workspace_GB");
    auto compute_calls=tf*Rational(1000000000000LL)*Rational(parallel)/(Rational(2)*params*(ins+outs));
    // Decode bandwidth bound: weights amortized across the declared batch; cache read per sequence.
    auto batch=Rational(count(a,"concurrent_sequences"));
    auto bandwidth_calls=bandwidth*Rational(parallel)/((weights/batch+kv/batch)*outs);
    capacity=std::min(compute_calls,bandwidth_calls);
    in=in+*it*number(p,"bytes_per_token");out=out+*ot*number(p,"bytes_per_token");
   }
   require(capacity>Rational(0),"capacity","Planning throughput must be positive");
   bool fits=required<=usable;failed=failed||!fits;maxmemory=std::max(maxmemory,required);
   auto replicas=(*rate/capacity).ceil();
   auto node_round=[&](Rational demand){return (demand/Rational(gpn/parallel)).ceil()*gpn;};
   auto g=node_round(Rational(replicas));auto lo=node_round(Rational((*rate/(capacity*(Rational(1)+band))).ceil()));auto hi=node_round(Rational((*rate/(capacity*(Rational(1)-band))).ceil()));
   total+=g;lower+=lo;upper+=hi;floor+=gpn;
   sh=sh+Rational(g)*number(a,"host_ram_GB_per_gpu");sl=sl+Rational(g)*number(a,"local_disk_GB_per_gpu");cp=cp+Rational(g)*Rational(count(a,"cpu_cores_per_gpu"));
   stages.push_back({{"stage_id",id},{"scenario_id",sid},{"model",model},{"service_objectives",s.value("service_objectives",Json::array())},{"assumptions",a},{"raw_gpus",g},{"replicas",replicas},{"capacity_per_replica",capacity.display(6)},{"capacity_unit",type=="training"?"token/s":"calls/s"},{"demand",rate->display(6)},{"weights_GB",weights.display(6)},{"kv_cache_GB_per_replica",kv.display(6)},{"required_GB_per_gpu",required.display(6)},{"memory_fit",fits},{"rule",type=="training"?"6*N FLOPs/token divided by effective dense compute. declared distributed efficiency":"min(compute bound, batched decode memory bound). approximate prefill/decode, no latency guarantee"}});
  }
  int lost=sc.value("failed_nodes",0);total+=lost*gpn;lower+=lost*gpn;upper+=lost*gpn;floor+=lost*gpn;
  nominal=std::max(nominal,total);upside=std::max(upside,lower);downside=std::max(downside,upper);memory_floor=std::max(memory_floor,floor);
  ingress=std::max(ingress,in);egress=std::max(egress,out);host=std::max(host,sh);local=std::max(local,sl);cores=std::max(cores,cp);
  scenarios.push_back({{"id",sid},{"raw_gpus",total},{"upside_gpus",lower},{"downside_gpus",upper},{"failure_nodes",lost}});
 }
 for(const auto &s:w["stages"])if(s["type"]=="data"||s["type"]=="checkpoint") {
  auto id=s["id"].get<std::string>();Rational bytes,read,write;bool known=false,read_known=false,write_known=false;
  for(const auto &sc:w["scenarios"]) {
   auto sid=sc["id"].get<std::string>();
   for(auto name:{"usable_bytes","retained_bytes","retained_upper_bound_bytes"})if(auto v=fact(r,id,sid,name)){bytes=std::max(bytes,*v);known=true;}
   if(auto v=fact(r,id,sid,"durable_write_GiBps")){write=std::max(write,*v*Rational(1073741824));write_known=true;}
  }
  for(auto [key,dest]:{std::pair{"read_rate",&read},std::pair{"write_rate",&write}})if(s["observations"].contains(key))if(auto v=quantity(s["observations"][key],"byte_rate",id)){*dest=std::max(*dest,*v);if(std::string(key)=="read_rate")read_known=true;else write_known=true;}
  if(!known)gaps.push_back(id+": usable storage capacity unresolved");
  storage.push_back({{"stage_id",id},{"tier",s.value("storage_tier",s["type"]=="checkpoint"?"parallel_file":"unspecified")},{"usable_bytes",bytes.display(0)},{"capacity_known",known},{"read_Bps",read_known?Json(read.display(3)):Json(nullptr)},{"write_Bps",write_known?Json(write.display(3)):Json(nullptr)},{"performance_basis","declared rates and checkpoint window. unspecified read/write demand is not qualified"}});
 }
 if(!gpu_stages)gaps.push_back("No active GPU workload");
 if(!comparison_platform.empty()) {
  r["hardware_estimate"]={{"platform",comparison_platform},{"raw_gpus",nominal},{"upside_gpus",upside},{"downside_gpus",downside},{"gpu_per_node",gpn},{"required_GB_per_gpu",maxmemory.display(6)},{"provided_GB_per_gpu",hbm.display(3)},{"status",failed?"fail":(!gaps.empty()||!p.value("assumptions_accepted",false))?"unknown":"conditional"},{"gaps",gaps},{"stage_calculations",stages},{"hardware",hw},{"basis","Workload estimate rounded to whole 8-GPU nodes. no RA anchor or downstream design tool platform compatibility implied"}};
  return;
 }
 auto anchors=architecture["anchors"];std::sort(anchors.begin(),anchors.end(),[](const Json&a,const Json&b){return a["gpus"]<b["gpus"];});
 auto service=number(p,"minimum_service_fraction");bool flexible=service<Rational(1);
 require(!flexible||p.value("accept_capacity_shortfall",false),"shortfall_acceptance","Explicitly accept reduced service before selecting a lower anchor");
 auto target=std::max<int64_t>(memory_floor,(Rational(nominal)*service).ceil());Json chosen=nullptr,next=nullptr;
 for(const auto &a:anchors)if(a["gpus"].get<int64_t>()>=target){chosen=a;break;}
 if(chosen.is_null())gaps.push_back("Demand exceeds largest supported architecture anchor");
 else for(const auto &a:anchors)if(a["gpus"]>chosen["gpus"]){next=a;break;}
 if(w.value("characterization",Json::object()).contains("guided_input") && (failed||!gaps.empty()||!p.value("assumptions_accepted",false))) {chosen=nullptr;next=nullptr;}
 auto status=failed?"fail":(!gaps.empty()||!p.value("assumptions_accepted",false))?"unknown":"conditional";
 Json plan={{"version","1.0"},{"status",status},{"evidence_basis",std::any_of(w["stages"].begin(),w["stages"].end(),[](const Json&s){return s.contains("planning")&&s["planning"].contains("reference");})?"declared_reference_and_analytical_planning":"analytical_planning"},{"catalog_digest",digest(cat)},{"catalog_version",cat["version"]},{"architecture",architecture},{"hardware",hw},{"policy",p},{"raw_gpus",nominal},{"upside_gpus",upside},{"downside_gpus",downside},{"selected_anchor",chosen},{"expansion_anchor",next},{"scenarios",scenarios},{"stage_calculations",stages},{"storage",storage},{"gaps",gaps},{"tenancy",w.value("tenancy","single")},{"host_ram_GB_required",host.display(3)},{"local_disk_GB_required",local.display(3)},{"cpu_cores_provision",cores.ceil()},{"required_GB_per_gpu",maxmemory.display(6)},{"provided_GB_per_gpu",hbm.display(3)},{"usable_GB_per_gpu",usable.display(3)},{"ingress_Gbps",(ingress*Rational(8)/Rational(1000000000)*number(p,"protocol_allowance")).display(6)},{"egress_Gbps",(egress*Rational(8)/Rational(1000000000)*number(p,"protocol_allowance")).display(6)},{"network_scope","Application tokens plus declared external transfers. customer RTT requirement remains independent. other payloads must be declared"},{"storage_fabric","Ethernet"},{"storage_network_policy","Physically dedicated storage network required. Converged networking is excluded."},{"expansion_trigger","Review when observed demand exceeds initial planning envelope or agreed service degrades. start procurement before declared lead time expires"},{"limitations",{"Analytical assumptions, not measured serving performance or guaranteed latency","Distinct stages use dedicated pools. scenarios reuse capacity only when declared non-overlapping","Host configuration and training scaling require later deployment validation"}}};
 plan["networks"]=network_plan(w,plan);
 if(!chosen.is_null()) {
  auto g=chosen["gpus"].get<int64_t>();plan["initial_gpus"]=g;plan["excess_gpus"]=std::max<int64_t>(0,g-nominal);plan["shortfall_gpus"]=std::max<int64_t>(0,nominal-g);
  plan["service_capacity_fraction"]=nominal?std::min(Rational(1),Rational(g,nominal)).display(6):"0";
  auto nodes=g/gpn;plan["nodes_or_trays"]=nodes;plan["racks"]=chosen.value("racks",Json(nullptr));
  plan["host_ram_GB_provided"]= (Rational(nodes)*number(hw,"host_ram_GB_per_node")).display(3);
  bool host_fit=Rational(nodes)*number(hw,"host_ram_GB_per_node")>=host&&Rational(nodes)*number(hw,"local_disk_GB_per_node")>=local&&Rational(nodes*hw["cpu_cores_per_node"].get<int>())>=cores;
  if(!host_fit){plan["gaps"].push_back("Selected host configuration needs more RAM, local disk or CPU than catalogue provision");plan["status"]="unknown";}
  if(plan["status"]=="conditional")r["candidates"].push_back({{"id","planning:factory"},{"stage_id","factory"},{"scenario_id","portfolio"},{"platform",platform},{"gpus",g},{"nodes",nodes},{"gpu_per_node",gpn},{"status","conditional"},{"profile_id",architecture["id"]},{"constraints",Json::array()},{"evidence_channel","public_planning"},{"memory",{{"required_GB_per_gpu",maxmemory.display(6)}}},{"host",{{"ram_GB",plan["host_ram_GB_provided"]}}},{"planning",true}});
 }
 // Whole-profile copies use dedicated, node-rounded allocations, including each copy's reserve.
 // This is a compute capacity estimate, not a jointly qualified tenant count.
 auto capacity_view=[&](const Json &anchor) -> Json {
  if(anchor.is_null())return nullptr;
  const auto count=anchor["gpus"].get<int64_t>();
  const bool resolved=plan["status"]=="conditional"&&nominal>0;
  return {{"gpus",count},{"supports_one_instance_compute",resolved?Json(count>=nominal):Json(nullptr)},
   {"equivalent_instances_compute",resolved?Json(count/nominal):Json(nullptr)},
   {"additional_instances_compute",resolved?Json(std::max<int64_t>(0,count/nominal-1)):Json(nullptr)},
   {"downside_instances_compute",resolved&&downside>0?Json(count/downside):Json(nullptr)},
   {"upside_instances_compute",resolved&&upside>0?Json(count/upside):Json(nullptr)}};
 };
 plan["workload_capacity"]={{"minimum_architecture",capacity_view(anchors.front())},{"selected_architecture",capacity_view(chosen)},
  {"tenant_limit",nullptr},
  {"basis","Whole copies of the same workload profile at coincident declared peaks, using dedicated node-rounded GPU pools and a separate reserve per copy. Sensitivity counts are planning envelopes, not confidence intervals."},
  {"qualification","Compute estimate only. Each copy also needs its storage, host resources and network capacity. tenancy and isolation require architectural validation. Architecture family is the selected catalogue profile, not an additional NCP compliance claim."}};
 // Keep independent unresolved diagnostics, but replace exact-match requests with the planning explanation.
 Json qs=Json::array();for(const auto &q:r["questions"])if(q.value("path","").find("/fingerprint")==std::string::npos)qs.push_back(q);r["questions"]=qs;
 r["knowledge_channel"]="public_planning";
 if(w.value("characterization",Json::object()).contains("guided_input")) r["guided_context"]={{"name",w["name"]},{"notes",w.value("notes",std::string(""))},{"characterization",w["characterization"]}};
 r["planning"]=plan;r["scope"]="Planning portfolio with explicit assumptions. measured profiles remain separate";r["domains"]["compute"]=plan["status"];
}
void add_planning(const Json &w,Json &r) {
 add_planning_impl(w,r);
 if(!w.contains("planning"))return;
 Json comparisons=Json::array();
 for(const auto &platform:{"HGX_B300","HGX_B200","HGX_H200"}) {
  Json comparison=r;add_planning_impl(w,comparison,platform);
  comparisons.push_back(comparison["hardware_estimate"]);
 }
 r["planning"]["hardware_comparison"]=comparisons;
}
}
