#pragma once
#include "application/characterization/guided.hpp"
namespace anubis {
inline Json assisted_input(const Json &w) {
 auto input=w.at("characterization").at("guided_input");
 for(auto key:{"name","notes","tenancy"})if(w.contains(key))input[key]=w[key];
 return input;
}
inline Json assisted_content(Json w) {w.erase("characterization");return w;}
inline Json assisted_review(const Json &w,const Json &catalog) {
 if(!w.contains("characterization")||!w["characterization"].contains("guided_input"))return {{"compatible",false},{"can_copy",false},{"differences",Json::array()},{"message","This workload has no assisted description. Continue editing or calculate in the advanced editor. A new assisted engagement will leave this workload unchanged."}};
 try {
  auto generated=guided_workload(assisted_input(w),catalog);
  auto original=assisted_content(w),replacement=assisted_content(generated);
  auto diff=Json::diff(replacement,original);Json preview=Json::array();
  for(const auto &change:diff){auto pointer=Json::json_pointer(change["path"]);preview.push_back({{"field",change["path"]},{"current",original.contains(pointer)?original.at(pointer):Json("Not present")},{"assisted_copy",replacement.contains(pointer)?replacement.at(pointer):Json("Not present")}});}
  return {{"conversion_preview",preview},{"compatible",diff.empty()},{"can_copy",true},{"differences",diff},{"assisted_copy",generated},{"message",diff.empty()?"This workload can be edited safely in either interface.":"The listed detailed settings are preserved in the advanced workload. Copilot updates are allowed only when they do not conflict with these settings."}};
 } catch(const std::exception &) {return {{"compatible",false},{"can_copy",false},{"differences",Json::array()},{"message","The saved assisted description cannot be reconstructed with the current catalogue. Continue editing or calculate in the advanced editor."}};}
}
inline Json assisted_merge(const Json &current,const Json &proposed,const Json &catalog) {
 auto review=assisted_review(current,catalog);require(review.value("can_copy",false),"assisted_conflict","This workload cannot be safely reconstructed. Continue in the advanced editor or create a separate assisted engagement.");
 auto base=assisted_content(review["assisted_copy"]),next=assisted_content(proposed);
 auto changes=Json::diff(base,next),custom=review["differences"];
 auto domain=[](const std::string &path){auto end=path.find('/',1);auto part=path.substr(0,end);return part=="/stages"||part=="/edges"||part=="/scenarios"?std::string("/workload graph"):part;};
 for(const auto &a:changes)for(const auto &b:custom)require(!((domain(a["path"])=="/workload graph"&&domain(b["path"])=="/workload graph")||a["path"]==b["path"]||a["path"].get<std::string>().starts_with(b["path"].get<std::string>()+"/")||b["path"].get<std::string>().starts_with(a["path"].get<std::string>()+"/")),"assisted_conflict","This proposal would change "+a["path"].get<std::string>()+" and conflict with your advanced setting "+b["path"].get<std::string>()+". Nothing was applied. Continue in the advanced editor or review a separate assisted copy.");
 auto merged=assisted_content(current).patch(changes);merged["characterization"]=current.value("characterization",Json::object());
 for(auto it=proposed["characterization"].begin();it!=proposed["characterization"].end();++it)merged["characterization"][it.key()]=it.value();
 if(!custom.empty())merged["characterization"]["advanced_modified"]=true;else merged["characterization"].erase("advanced_modified");
 return merged;
}
}
