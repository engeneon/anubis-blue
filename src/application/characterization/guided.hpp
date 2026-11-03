#pragma once
#include "compiler/compiler.hpp"
#include "compiler/planning.hpp"
#include "application/characterization/readiness.hpp"
namespace anubis {
// Pure transformation shared by UI and API clients. No narrative interpretation.
inline Json guided_workload(const Json &b,const Json &pack) {
 keys(b,{"name","components","overlap","tenancy","accepted","architecture","sensitivity","notes","network","input_basis"},"");
 require(!text(b,"name").empty(),"name","Enter the customer workload name");
 require(b.contains("components")&&b["components"].is_array()&&!b["components"].empty()&&b["components"].size()<=16,"components","Choose one to sixteen application components");
 auto overlap=b.value("overlap",std::string("unknown")),tenancy=b.value("tenancy",std::string("single"));
 require(overlap=="yes"||overlap=="no"||overlap=="unknown","overlap","Choose overlap, separate windows or not sure");
 require(tenancy=="single"||tenancy=="multi","tenancy","Choose one organisation or multiple tenants");
 require(b.contains("accepted")&&b["accepted"].is_boolean(),"acceptance","Review the planning assumptions");
 Json policy=pack["policy"];policy["assumptions_accepted"]=b["accepted"];
 policy["architecture"]=b.value("architecture",policy["architecture"].get<std::string>());
 policy["sensitivity_percent"]=b.value("sensitivity",std::string("30"));
 Json w={{"schema_version","1.0"},{"name",b["name"]},{"tenancy",tenancy},{"notes",b.value("notes",std::string(""))},{"stages",Json::array()},{"edges",Json::array()},{"scenarios",Json::array()},{"planning",policy}};
 Json follow=Json::array(),map=Json::array();int i=0;
 auto observation=[&](const Json &c,const char *key,const char *unit,const char *fallback="") {
  auto v=c.value(key,std::string(fallback));if(v.empty())v=fallback;if(v.empty())return Json{{"state","unknown"}};
  auto n=Rational::decimal(v);require(n>=Rational(0),"input",std::string(key)+" cannot be negative");
  bool supplied=c.contains(key)&&!c[key].get<std::string>().empty();
  Json result={{"state",supplied?"estimated":"assumed"},{"value",v},{"unit",unit},{"origin",supplied?"customer":"template"},{"source",supplied?"Consultant intake":"Anubis guided-1.0 preset"},{"accepted",b["accepted"]}};
  if(supplied && b.contains("input_basis")) {
   const auto &basis=b["input_basis"];require(basis.is_object(),"basis","Input basis must be an object");
   auto field="components."+std::to_string(i-1)+"."+(std::string(key)=="extra_calls"?"calls":key);
   Json entry=basis.value(field,basis.value("components",Json()));
   if(!entry.is_null()) {auto kind=text(entry,"basis");require(kind=="planning_assumption"||kind=="customer_statement"||kind=="extracted_observation","basis","Invalid accepted input basis");result["state"]=kind=="planning_assumption"?"assumed":"estimated";result["origin"]="agent";result["source"]="Consultant reviewed "+kind+". Source "+entry.value("source_id",std::string("planning assumption"));}
  }
  return result;
 };
 for(const auto &c:b["components"]) {
  keys(c,{"name","pattern","location","demand_mode","rate","users","interval","jobs","window","calls","input_tokens","output_tokens","model","tokens","days","storage_tb","growth_gb_day","horizon_days","retrieval","service_seconds","relationship","dedicated","sizing_method","reference_demand","reference_unit","reference_gpus","reference_memory","reference_h200","reference_b200","reference_b300","reference_source","reference_independent","reference_includes_support","reference_accepted"},"/components");
  auto id="component_"+std::to_string(++i),pattern=text(c,"pattern"),name=text(c,"name");
  require(!name.empty()&&name.size()<=160,"component_name","Name each component (up to 160 characters)");
  bool known=false;for(const auto &p:pack["patterns"])if(p["id"]==pattern)known=true;
  require(known,"pattern","Choose a catalogue application pattern");
  auto location=c.value("location",std::string("local"));require(location=="local"||location=="external"||location=="unknown","location","Choose local, external or not sure");
  auto relationship=c.value("relationship",std::string("independent"));require(relationship=="independent"||relationship=="after"||relationship=="alongside"||relationship=="conditional","relationship","Choose a component relationship");
  require(!(overlap=="no"&&relationship=="alongside"),"schedule","Alongside components cannot use separate operating windows");
  bool supported=pattern=="direct"||pattern=="retrieval"||pattern=="agent"||pattern=="batch"||pattern=="training";
  bool reference=c.value("sizing_method",std::string())=="reference";
  auto type=reference&&location=="local"?"cpu":location=="external"?"cpu":!supported||location!="local"?"unsupported":pattern=="training"?"training":pattern=="batch"?"batch":"inference";
  Json s={{"id",id},{"name",name},{"type",type},{"observations",Json::object()},{"notes",location=="external"?"External compute excluded. Connectivity and storage remain separate requirements.":"Application component: "+pattern}};
  if(reference&&location=="local") {
   auto single=b;single["components"]=Json::array({c});auto ready=gpu_readiness(single);
   if(!ready["ready"].get<bool>()){s["type"]="unsupported";s["notes"]="Reference GPU inputs incomplete. No count inferred.";for(const auto&issue:ready["missing"])follow.push_back(name+": "+issue["label"].get<std::string>()+" — "+issue["reason"].get<std::string>());}
   else {s["planning"]=Json::object();for(const auto*k:{"host_ram_GB_per_gpu","local_disk_GB_per_gpu","cpu_cores_per_gpu"})s["planning"][k]=pack["serving"][k];
   s["planning"]["reference"]={{"demand",c["reference_demand"]},{"unit",c["reference_unit"]},{"group_gpus",c["reference_gpus"]},{"memory_GB",c["reference_memory"]},{"capacities",{{"HGX_H200",c["reference_h200"]},{"HGX_B200",c["reference_b200"]},{"HGX_B300",c["reference_b300"]}}},{"source",c["reference_source"]},{"accepted",c["reference_accepted"]},{"independent_groups",c["reference_independent"]}};
   s["notes"]="Consultant supplied reference capacity. Full groups replicated for independent work. Not text-token sizing.";}
  } else if(type==std::string("unsupported")) {
   std::string next=pattern=="other"?"Obtain solver-specific throughput, mesh size, solver steps, memory and completion deadline.":"Obtain workload-specific model, throughput, memory and completion-window measurements.";
   follow.push_back(name+": "+next);s["notes"]=next;
  } else if(location=="local") {
   auto a=pack["serving"];a["model"]=c.value("model",std::string("dense8b"));
   require(planning_catalog()["models"].contains(a["model"].get<std::string>()),"model","Choose a supported model preset");
   if(pattern=="training")a["parallel_gpus"]=8;
   s["planning"]=a;auto &o=s["observations"];
   if(pattern=="training") {o["tokens"]=observation(c,"tokens","token");o["window"]=observation(c,"days","day");o["effective_fraction"]=observation(Json::object(),"effective_fraction","ratio",".85");follow.push_back(name+": Confirm checkpoint size, save window, retention and data-loading bandwidth in Refine estimate.");}
   else {
    auto mode=c.value("demand_mode",std::string("rate"));require(mode=="rate"||mode=="users","demand_mode","Choose request rate or users");
    if(pattern=="batch") {o["jobs"]=observation(c,"jobs","count");o["window"]=observation(c,"window","hour");o["calls_per_job"]=observation(c,"calls","ratio","1");}
    else {if(mode=="users"){o["users"]=observation(c,"users","count");o["interval"]=observation(c,"interval","s");}else o["rate"]=observation(c,"rate","request/min");
     auto calls=c.value("calls",std::string(pattern=="agent"?"":"1"));
     if(calls.empty()&&pattern!="agent")calls="1";
     if(calls.empty())o["extra_calls"]={{"state","unknown"}};
     else {auto n=Rational::decimal(calls);require(n>=Rational(1),"calls","Calls per request must be at least one");o["extra_calls"]=observation(Json{{"extra_calls",(n-Rational(1)).display(6)}},"extra_calls","ratio");}
    }
    o["input_tokens"]=observation(c,"input_tokens","token","2000");o["output_tokens"]=observation(c,"output_tokens","token","500");
    auto target=c.value("service_seconds",std::string(""));if(!target.empty())s["service_objectives"]=Json::array({{{"metric","completion"},{"percentile","95"},{"target",observation(c,"service_seconds","s")},{"boundary","Model request received to completed response. external retrieval and network excluded"}}});
   }
  }
  if(pattern=="retrieval"||pattern=="agent") {
   auto retrieval=c.value("retrieval",std::string("unknown"));require(retrieval=="external"||retrieval=="local"||retrieval=="none"||retrieval=="unknown","retrieval","Choose retrieval placement");
   if((retrieval=="local"||retrieval=="unknown")&&!reference) {auto rid=id+"_retrieval";w["stages"].push_back({{"id",rid},{"name",name+" retrieval and indexing"},{"type","unsupported"},{"observations",Json::object()},{"notes","Confirm embedding model, index refresh volume, CPU/GPU placement and search throughput. Not included in text GPU estimate."}});follow.push_back(name+": retrieval and indexing resources need separate measurements. text GPU count is partial.");}
  }
  w["stages"].push_back(s);
  auto storage=c.value("storage_tb",std::string(""));
  if(!storage.empty()) {
   auto tb=Rational::decimal(storage);require(tb>=Rational(0),"storage","Storage cannot be negative");
   auto growth=c.value("growth_gb_day",std::string("")),horizon=c.value("horizon_days",std::string("365"));
   if(horizon.empty())horizon="365";
   if(!growth.empty()){auto g=Rational::decimal(growth),h=Rational::decimal(horizon);require(g>=Rational(0)&&h>Rational(0),"growth","Growth must be nonnegative and horizon positive");tb=tb+g*h/Rational(1000);}
   w["stages"].push_back({{"id",id+"_data"},{"name",name+" retained data"},{"type","data"},{"storage_tier","object"},{"observations",{{"bytes",observation(Json{{"bytes",tb.display(6)}},"bytes","TB")},{"free_fraction",observation(Json::object(),"free_fraction","ratio",".2")}}}});
  }
  map.push_back({{"id",id},{"name",name},{"pattern",pattern},{"location",location},{"retrieval",c.value("retrieval",std::string("unknown"))},{"relationship",relationship},{"support",location=="external"?"External compute":reference&&location=="local"?"Reference capacity sizing":supported&&location=="local"?"Analytical sizing":"Specialist measurements required"}});
 }
 bool dedicated=false;for(const auto &c:b["components"]) {if(c.contains("dedicated"))require(c["dedicated"].is_boolean(),"dedicated","Dedicated capacity must be boolean");dedicated=dedicated||c.value("dedicated",false);}
 if(overlap=="no"&&!dedicated) {for(const auto &m:map){Json active=Json::array();auto id=m["id"].get<std::string>();for(const auto&s:w["stages"])if(s["type"]=="data"||s["id"].get<std::string>().starts_with(id+"_")||s["id"]==id)active.push_back(s["id"]);w["scenarios"].push_back({{"id",id},{"name",m["name"]},{"active_stages",active},{"multiplier","1"},{"failed_nodes",0}});}}
 else {w["scenarios"].push_back({{"id","coincident"},{"name","Simultaneous or reserved capacity"},{"multiplier","1"},{"failed_nodes",0}});if(overlap=="unknown"&&map.size()>1)follow.push_back("Overlap unknown: simultaneous demand assumed until schedules are confirmed.");}
 w["characterization"]={{"guided_input",b},{"gpu_readiness",gpu_readiness(b)},{"pack_version",pack["version"]},{"pack_digest",digest(pack)},{"components",map},{"follow_up",follow}};
 validate_workload(w);return w;
}
}
