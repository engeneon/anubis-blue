#pragma once
#include "domain/json.hpp"
#include <set>
namespace anubis {
inline Json characterize(const Json &b, const Json &catalog) {
 keys(b,{"name","activities","overlap","tenancy"},"");
 const auto name=text(b,"name"); require(!name.empty()&&name.size()<=240,"name","Name the customer workload (1–240 characters)");
 require(b.contains("activities")&&b["activities"].is_array()&&!b["activities"].empty()&&b["activities"].size()<=16,"activities","Describe one to sixteen activities");
 auto overlap=b.value("overlap",std::string("unknown")),tenancy=b.value("tenancy",std::string("unknown"));
 require(overlap=="unknown"||overlap=="yes"||overlap=="no","overlap","Choose yes, no or unknown");
 require(tenancy=="unknown"||tenancy=="single"||tenancy=="multi","tenancy","Choose single, multi or unknown");
 Json out={{"catalog_version",catalog["version"]},{"catalog_digest",digest(catalog)},{"answers",b},{"activities",Json::array()},{"relationships",Json::array()},{"questions",Json::array()},{"patterns",Json::array()}};
 Json stages=Json::array(); std::set<std::string> all;
 int index=0;
 for (const auto &a:b["activities"]) {
  keys(a,{"name","answers","location","calls","schedule","relationship","predecessor","sharing"},"/activities");
  auto label=text(a,"name"); require(!label.empty()&&label.size()<=160,"activity_name","Name each activity (1–160 characters)");
  require(a.contains("answers")&&a["answers"].is_object(),"answers","Activity answers must be an object");
  for(auto it=a["answers"].begin();it!=a["answers"].end();++it) { bool found=false;for(const auto &q:catalog["questions"])if(q["id"]==it.key())found=true; require(found,"answer","Unknown discovery question: "+it.key()); }
  Json normalized=Json::object();
  for(const auto &q:catalog["questions"]) {auto id=q["id"].get<std::string>();auto v=a["answers"].value(id,std::string("unknown"));require(v=="yes"||v=="no"||v=="unknown","answer","Choose yes, no or unknown");normalized[id]=v;if(v=="unknown")out["questions"].push_back(label+": "+q["label"].get<std::string>());}
  Json modifiers=Json::object();
  for(const auto &q:catalog["modifiers"]) {auto id=q["id"].get<std::string>();auto v=a.value(id,std::string(id=="relationship"?"independent":"unknown"));bool valid=false;for(const auto &option:q["options"])if(option==v)valid=true;require(valid,"modifier","Invalid "+id);modifiers[id]=v; if(v=="unknown")out["questions"].push_back(label+": "+q["label"].get<std::string>());}
  auto yes=[&](const char *k){return normalized[k]=="yes";};
  Json matches=Json::array();auto add=[&](const char *id,const char *why){matches.push_back({{"id",id},{"reason",why}});all.insert(id);};
  if(yes("text")&&!yes("search")&&!yes("agent"))add("direct","Text model processing without confirmed retrieval or agent orchestration");
  if(yes("search"))add("retrieval","Information retrieval is part of this activity");
  if(yes("agent"))add("agent","Tool use or multi-step orchestration is present");
  for(const auto *id:{"batch","stream","generation","adaptation","training"})if(yes(id))add(id,"Confirmed by the activity answer");
  if(matches.empty())out["questions"].push_back(label+": No core pattern confirmed. Describe the missing activity; do not force a match.");
  auto loc=modifiers["location"].get<std::string>();
  if(loc=="mixed")out["questions"].push_back(label+": Split local and external processing into separate activities before sizing.");
  if(modifiers["calls"]=="one"&&yes("agent"))out["questions"].push_back(label+": Confirm one model call despite tool use or orchestration; tools may be deterministic.");
  if(yes("adaptation")&&yes("training"))out["questions"].push_back(label+": Separate fine-tuning from pretraining, or confirm the intended training method.");
  const auto id="activity_"+std::to_string(++index);
  Json flow=Json::array(); if(yes("stream"))flow.push_back("Receive stream");if(yes("search"))flow.push_back("Search information"); if(yes("agent"))flow.push_back("Choose actions / use tools / possible repeated calls");if(yes("text"))flow.push_back("Process text with model");if(yes("generation"))flow.push_back("Generate media");if(yes("adaptation"))flow.push_back("Adapt existing model");if(yes("training"))flow.push_back("Train model");if(yes("indexing"))flow.push_back("Build or refresh index (schedule to confirm)");
  flow.push_back("Return or store output");
  auto relation=modifiers["relationship"].get<std::string>();
  if(relation!="independent") {require(index>1&&a.contains("predecessor")&&a["predecessor"].is_number_integer(),"relationship","Choose an earlier activity for this relationship");int pred=a["predecessor"].get<int>();require(pred>=0&&pred<index-1,"relationship","Relationship must point to an earlier activity");out["relationships"].push_back({{"from","activity_"+std::to_string(pred+1)},{"to",id},{"kind",relation}});require(!(overlap=="no"&&relation=="alongside"),"overlap_conflict","Alongside work conflicts with no overlap; correct the arrangement");}
  bool specialist=yes("stream")||yes("generation")||yes("adaptation");
  std::string support=loc=="external"?"External compute excluded; connectivity and data requirements remain":loc!="local"?"Placement unresolved; no local GPU allocation inferred":specialist?"Specialised sizing model required; no text-token substitution":"Existing engine components; model, demand and supporting-resource inputs still required";
  out["activities"].push_back({{"id",id},{"name",label},{"patterns",matches},{"flow",flow},{"modifiers",modifiers},{"sizing_support",support},{"indexing",yes("indexing")}});
  // Discovery is descriptive. Missing quantitative work is explicitly unsupported, never zero cost.
  stages.push_back({{"id",id},{"name",label},{"type","unsupported"},{"observations",Json::object()},{"notes",support+". Characterisation only; refine before quantitative sizing."}});
 }
 for(const auto &id:all)out["patterns"].push_back(id);
 if(overlap=="unknown"&&index>1)out["questions"].push_back("Can these activities be busy at the same time? Confirm before pooling capacity.");
 if(tenancy=="unknown")out["questions"].push_back("Will this factory serve one organisation or separate customers?");
 out["status"]=out["questions"].empty()?"characterized":"needs_clarification";
 out["arrangement_note"]="Proposed activity order for consultant confirmation. Arrows do not imply a measured call count, latency or safe resource sharing.";
 out["overlap"]=overlap;out["tenancy"]=tenancy;
 Json scenarios=Json::array(); if(overlap=="no")for(const auto &s:stages)scenarios.push_back({{"id",s["id"]},{"name",s["name"]},{"multiplier","1"},{"failed_nodes",0},{"active_stages",Json::array({s["id"]})}});
 else scenarios.push_back({{"id","unresolved_overlap"},{"name","Overlap requires sizing review"},{"multiplier","1"},{"failed_nodes",0}});
 out["workload"]={{"schema_version","1.0"},{"name",name},{"stages",stages},{"edges",Json::array()},{"scenarios",scenarios},{"notes","Architecture discovery only. No GPU quantity has been inferred. Refine each activity before compiling."}};
 if(tenancy!="unknown")out["workload"]["tenancy"]=tenancy;
 out["workload"]["characterization"]={{"catalog_version",catalog["version"]},{"catalog_digest",digest(catalog)},{"answers",b}};
 return out;
}
}
