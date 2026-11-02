#pragma once
#include "persistence/store.hpp"
#include <set>

namespace anubis {
inline Json closure_review(Store &store,const Json &engagement) {
 auto id=engagement["id"].get<std::string>();
 auto drafts=store.list("draft",id),sessions=store.list("copilot_session",id),results=store.list("result",id),projections=store.list("projection",id),proposals=store.list("copilot_proposal",id,-1),sources=store.list("copilot_source",id,-1);
 auto latest=[](const Json &rows){return rows.empty()?Json():rows[0];};
 auto draft=latest(drafts),session=latest(sessions),result=latest(results);
 Json input=Json::object();std::string basis="accepted workload";
 if(!draft.is_null()&&draft["data"].contains("characterization"))input=draft["data"]["characterization"].value("guided_input",Json::object());
 else if(!session.is_null())input=session["data"].value("input",Json::object());
 if(input.value("components",Json::array()).empty()&&!proposals.empty()&&proposals[0]["data"].value("state",std::string(""))=="proposed") {input=proposals[0]["data"].value("preview",Json::object());basis="unaccepted proposal. Its findings require consultant review";}
 auto components=input.value("components",Json::array());int supported=0,specialist=0;
 for(const auto &component:components){auto pattern=component.value("pattern",std::string(""));if(std::set<std::string>{"stream","generation","adaptation","other"}.contains(pattern))++specialist;else if(component.value("location",std::string("unknown"))!="external")++supported;}
 bool running=false;for(const auto &job:store.list("job",id,-1))if(std::set<std::string>{"queued","running","cancel_requested"}.contains(job["data"].value("state",std::string(""))))running=true;
 bool stale=false;if(!result.is_null()){auto revision=store.get(result["data"]["revision_id"]);stale=draft.is_null()||revision["data"]["source_draft"]!=draft["id"]||revision["data"]["source_version"]!=draft["version"];}
 bool matching_projection=false;if(!result.is_null()&&!stale)for(const auto &pr:projections)if(pr["data"]["result_id"]==result["id"])matching_projection=true;
 std::string state="work_remaining",reason="No completed handoff is established. Missing a projection alone does not prove that sizing is impossible.";
 bool recommend=false;
 if(specialist){state=supported?"partial_scope":"specialist_required";reason=supported?"Some components require specialist methods. Any supported compute estimate is only a subtotal, not a complete workload design.":"The characterised computation is outside the assisted sizing methods. Specialist measurements and a suitable sizing method are required. Any advanced calculations or existing projections must be assessed separately before declaring a complete design handoff.";recommend=true;}
 else if(components.empty()&&result.is_null()){state="insufficient_description";reason="The available information does not yet establish a workload that can be sized. The consultant may gather more information or conclude with a status report.";recommend=!sources.empty()||!proposals.empty();}
 else if(result.is_null()&&!session.is_null()&&session["data"].contains("ready_for_estimate")&&!session["data"]["ready_for_estimate"].get<bool>()){state="insufficient_evidence";reason="Essential workload details remain unresolved. Continue collecting evidence, or record why the current engagement should conclude without final requirements.";recommend=true;}
 else if(stale){state="stale_calculation";reason="Saved workload changes are newer than the latest calculation. Previous results are historical and cannot establish current requirements.";}
 else if(matching_projection){state="handoff_available";reason="A projection exists for the current calculation. Normal requirements-delivery completion is available, subject to its qualifications.";}
 Json snapshot={{"draft",draft},{"session",session},{"result",result},{"projections",projections},{"proposals",proposals},{"sources",sources}};
 Json assessment={{"state",state},{"reason",reason},{"basis",basis},{"offer_status_closure",recommend},{"running_jobs",running},{"stale_result",stale},{"snapshot",snapshot}};
 assessment["review_digest"]=digest(assessment);
 std::string report="ENGAGEMENT FINAL STATUS REPORT\n"+engagement["data"]["name"].get<std::string>()+"\n\nOutcome: concluded without a design handoff. This does not mean requirements were delivered or the architecture was approved.\n\nAssessment: "+reason+"\nBasis: "+basis+"\n\nWorkload scope\n";
 for(const auto &component:components)report+="- "+component.value("name",std::string("Unnamed activity"))+": "+component.value("pattern",std::string("unknown"))+". Compute location: "+component.value("location",std::string("unknown"))+".\n";
 if(components.empty())report+="- No confirmed component description available.\n";
 report+="\nAccepted facts from the latest saved Copilot session\n";
 auto facts=session.is_null()?Json::array():session["data"].value("facts",Json::array());
 for(const auto &f:facts)report+="- "+f.value("activity",std::string(""))+" / "+f.value("concept",std::string(""))+": "+f.value("value",std::string("unknown"))+" "+f.value("unit",std::string(""))+(f.value("period_value",std::string("")).empty()?std::string(""):" per "+f.value("period_value",std::string(""))+" "+f.value("period_unit",std::string("")))+" ["+f.value("status",std::string("unknown"))+"]"+". Source: "+f.value("quote",std::string("not recorded"))+"\n";
 if(facts.empty())report+="- No accepted fact ledger is available. Source statements and unaccepted proposals are preserved separately in the complete record, not promoted to accepted facts.\n";
 report+="\nOutstanding information and next steps\n";
 if(specialist)report+="- Obtain application and solver versions, representative work-item size, measured GPU throughput and memory use, required completion windows and concurrency. Use a qualified specialist sizing method before proposing hardware counts.\n";
 if(!session.is_null()&&session["data"].contains("next_question"))report+="- Last recorded clarification: "+session["data"]["next_question"].get<std::string>()+"\n";
 if(!proposals.empty()){
  report+="- Latest proposal review status: "+proposals[0]["data"].value("state",std::string("unknown"))+".\n";
  for(const auto &question:proposals[0]["data"].value("questions",Json::array()))report+="  - "+question.value("question",std::string("Unspecified follow-up"))+"\n";
 }
 report+="- Reopen the engagement when evidence or a supported sizing method becomes available.\n\nExisting calculations\n";
 if(result.is_null())report+="No calculation result is available. No GPU count is inferred from missing measurements.\n";
 else {
  report+="Saved result: "+result["id"].get<std::string>()+". "+(stale?"Historical result predating newer workload edits.":"Retained with its original qualifications, not promoted to a final design requirement by this closure.")+"\n";
  auto planning=result["data"]["result"].value("planning",Json::object());
  for(const auto &[key,label]:std::vector<std::pair<std::string,std::string>>{{"status","Calculation status"},{"raw_gpus","Recorded workload GPU estimate"},{"initial_gpus","Recorded selected factory GPU count"},{"required_GB_per_gpu","Recorded GPU memory requirement (GB per GPU)"}})if(planning.contains(key)&&!planning[key].is_null())report+="- "+label+": "+(planning[key].is_string()?planning[key].get<std::string>():planning[key].dump())+"\n";
  for(const auto &gap:planning.value("gaps",Json::array()))report+="- Calculation limitation: "+(gap.is_string()?gap.get<std::string>():gap.dump())+"\n";
  report+="Any partial estimates retain their original scope. Full numerical details are preserved in the complete closure record.\n";
 }
 report+="\nSupporting sources, proposals, workload and any existing calculations/projections are preserved in the complete closure record. Unaccepted proposals remain unaccepted.\n";
 assessment["report_text"]=report;return assessment;
}
}
