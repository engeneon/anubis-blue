#pragma once
#include "compiler/planning.hpp"
namespace anubis {
// Shared preflight for GUI and API. Missing business demand is never filled silently.
inline Json gpu_readiness(const Json &b) {
 require(b.is_object(),"readiness_input","Supply an intake object");
 if(b.contains("name"))require(b["name"].is_string(),"readiness_input","Workload name must be text");
 if(b.contains("components"))require(b["components"].is_array()&&b["components"].size()<=16,"readiness_input","Supply at most 16 components");
 Json missing=Json::array(), assumptions=Json::array();int local=0,index=0;
 auto add=[&](int i,const std::string &field,const std::string &label,const std::string &why,const std::string &kind="input"){
  missing.push_back({{"component",i},{"field",field},{"label",label},{"reason",why},{"kind",kind}});
 };
 auto positive=[](const Json& c,const char*k){try{auto v=c.value(k,std::string(""));return !v.empty()&&Rational::decimal(v)>Rational(0);}catch(...){return false;}};
 if(b.value("name",std::string()).empty())add(-1,"name","Customer workload name","Name this engagement.");
 auto cs=b.value("components",Json::array());if(!cs.is_array()||cs.empty())add(-1,"components","Application pattern","Choose the activities that require sizing.");
 if(cs.is_array())for(const auto &c:cs){require(c.is_object(),"readiness_input","Each component must be an object");for(auto it=c.begin();it!=c.end();++it)require((it.key()=="dedicated"||it.key()=="reference_independent"||it.key()=="reference_includes_support"||it.key()=="reference_accepted")?it.value().is_boolean():it.value().is_string(),"readiness_input","Component quantities must be text. Confirmations must be boolean.");int i=index++;auto location=c.value("location",std::string("unknown")),pattern=c.value("pattern",std::string());
  if(c.value("name",std::string()).empty())add(i,"name","Component name "+std::to_string(i+1),"Name this activity.");
  if(location!="local"&&location!="external"){add(i,"location","Compute location "+std::to_string(i+1),"Confirm which factory supplies this compute.");continue;}
  if(location=="external")continue;
  local++;
  if(c.value("sizing_method",std::string())=="reference"){
   for(auto [key,label]:{std::pair{"reference_demand","Peak work units per second"},{"reference_memory","Required GPU memory in GB"},{"reference_gpus","GPUs per reference group"}})if(!positive(c,key))add(i,key,label,"Supply a positive reference-sizing value.");
   if(positive(c,"reference_gpus")){auto n=Rational::decimal(c["reference_gpus"]);if(n!=Rational(n.ceil())||n>Rational(1024)||(n.ceil()<8?8%n.ceil()!=0:n.ceil()%8!=0))add(i,"reference_gpus","GPUs per reference group","Use 1, 2, 4, 8 or a multiple of 8 GPUs, up to 1024, to preserve whole groups within eight-GPU nodes.");}
   for(auto [key,label]:{std::pair{"reference_h200","H200 work units per second per group"},{"reference_b200","B200 work units per second per group"},{"reference_b300","B300 work units per second per group"}})if(!positive(c,key))add(i,key,label,"Supply capacity for this hardware. Do not extrapolate another GPU silently.");
   for(auto [key,label]:{std::pair{"reference_unit","Work unit"},{"reference_source","Reference source and conditions"}})if(c.value(key,std::string()).empty())add(i,key,label,"Identify matching work units and the model, configuration and source assumptions.");
   if(!c.value("reference_independent",false))add(i,"reference_independent","Independent reference groups can serve this demand","Confirm replication of complete tested or assumed groups. Do not linearly extrapolate a single distributed job.");
   if((pattern=="retrieval"||pattern=="agent")&&c.value("retrieval",std::string("unknown"))!="external"&&c.value("retrieval",std::string("unknown"))!="none")
    if(c.value("retrieval",std::string("unknown"))!="local"||!c.value("reference_includes_support",false))add(i,"retrieval","Search and indexing location "+std::to_string(i+1),"Confirm local placement and that the reference includes retrieval/indexing, or place that service outside this factory.");
   if(!c.value("reference_accepted",false))add(i,"reference_accepted","I accept this reference capacity and its scope","Review the source and assumptions before using this capacity.");
   if(b.contains("architecture")&&!b["architecture"].get<std::string>().empty()){auto catalog=planning_catalog();for(const auto&a:catalog["architectures"])if(a["id"]==b["architecture"]&&a["platform"]!="HGX_H200"&&a["platform"]!="HGX_B200"&&a["platform"]!="HGX_B300")add(-1,"architecture","Infrastructure deployment profile","Reference capacities cover H200, B200 and B300 only. Select one of those profiles.");}
   assumptions.push_back("Reference capacity is supplied by the consultant. It is not an Anubis benchmark qualification.");continue;
  }
  if(pattern!="direct"&&pattern!="retrieval"&&pattern!="agent"&&pattern!="batch"&&pattern!="training"){
   add(i,"sizing_method","Sizing method","This activity needs reference demand, capacity, memory and source information. Text-token equations do not size it.","unsupported_without_reference");continue;
  }
  auto model=c.value("model",std::string("dense8b"));if(!planning_catalog()["models"].contains(model))add(i,"model","Model preset","Choose a supported model or use reference capacity.");
  if(pattern=="training"){
   if(!positive(c,"tokens"))add(i,"tokens","Training tokens","Tokenised dataset × repetitions, not the number of examples.");
   if(!positive(c,"days"))add(i,"days","Training deadline in days","Supply the available completion window.");
  }else{
   if(pattern=="batch"){
    if(!positive(c,"jobs"))add(i,"jobs","Jobs per window","Supply the number of items to finish.");
    if(!positive(c,"window"))add(i,"window","Completion window in hours","Supply the time available for those items.");
   }else if(c.value("demand_mode",std::string("rate"))=="users"){
    if(!positive(c,"users"))add(i,"users","Active users","Count users active in the busy period, not total registered users.");
    if(!positive(c,"interval"))add(i,"interval","Seconds between requests per user","Supply the request interval for those active users.");
   }else if(!positive(c,"rate"))add(i,"rate","Peak requests per minute","Supply a busy-period rate. A daily volume or employee count is not a peak rate.");
   if(pattern=="agent"&&!positive(c,"calls"))add(i,"calls","Model calls per request or job","Supply planning call expansion including tool loops and retries.");
   for(auto [key,label]:{std::pair{"calls","Model calls per request or job"},{"input_tokens","Input tokens per model call"},{"output_tokens","Output tokens per model call"}}){
    if(!c.value(key,std::string()).empty()&&!positive(c,key))add(i,key,label,"Enter a positive number.");
   }
  }
  if(pattern!="training"){
   if(positive(c,"calls")&&Rational::decimal(c["calls"])<Rational(1))add(i,"calls","Model calls per request or job","Use at least one model call.");
   auto token=[&](const char*k,const char*def){return Rational::decimal(c.value(k,std::string()).empty()?std::string(def):c[k].get<std::string>());};
   try{if(token("input_tokens","2000")+token("output_tokens","500")>Rational(8192))add(i,"input_tokens","Input tokens per model call","Input plus output exceeds the 8192-token guided preset. Reduce only if justified, or configure a larger context in the advanced editor.");}catch(...){}
  }
  if(pattern=="retrieval"||pattern=="agent"){
   auto retrieval=c.value("retrieval",std::string("unknown"));if(retrieval!="external"&&retrieval!="none")add(i,"retrieval","Search and indexing location "+std::to_string(i+1),"Local or unconfirmed retrieval leaves a partial GPU result. Use a scoped reference that includes local support, or confirm it is outside this factory.");
  }
  assumptions.push_back(c.value("name",std::string("Activity"))+": review model, token and memory defaults. Defaults are assumptions, not measurements.");
 }
 if(local==0&&!cs.empty())add(-1,"components","Local GPU workload","No confirmed local GPU activity. Outside model GPUs are excluded. Add a real local requirement only if the customer needs one.","scope");
 return {{"ready",missing.empty()},{"missing",missing},{"assumptions",assumptions},{"meaning",missing.empty()?"Inputs support a GPU calculation. Accept assumptions and calculate to check capacity and memory feasibility.":"A complete GPU estimate is not yet possible. Complete the fields below before calculating."}};
}
}
