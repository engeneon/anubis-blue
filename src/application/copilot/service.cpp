#include "application/copilot/explanation.hpp"
#include "application/characterization/assisted.hpp"
#include "application/service.hpp"
#include "application/copilot/facts.hpp"
#include "adapters/model_transport.hpp"
#include <fstream>
#include <chrono>
namespace anubis {
static Json load_catalog(const std::string &root) {std::ifstream f(root+"/knowledge/guided-intake.json");return parse(std::string(std::istreambuf_iterator<char>(f),{}));}
static Json public_profile(Json r) {r["data"].erase("health_details");return r;}
Reply Service::copilot_dispatch(const Actor &a,const std::string &method,const std::vector<std::string>&p,const Json&b,const std::string&) {
 auto id=p.size()>1?p[1]:"",op=p.size()>2?p[2]:"";auto catalog=load_catalog(root_); std::ifstream lf(root_+"/knowledge/workload-interpretation.json");auto library=parse(std::string(std::istreambuf_iterator<char>(lf),{}));
 const bool disabled=std::getenv("ANUBIS_COPILOT_DISABLED")&&std::string(std::getenv("ANUBIS_COPILOT_DISABLED"))=="1";
 const auto now=std::chrono::duration_cast<std::chrono::seconds>(std::chrono::system_clock::now().time_since_epoch()).count();
 if(method=="POST"&&(op=="turns"||op=="test"||op=="mcp-import"||(p[0]=="copilot-explanations"&&!b.value("profile_id",std::string()).empty()))) {
  int limit=200;if(const char *value=std::getenv("ANUBIS_AI_DAILY_CALL_LIMIT"))limit=std::stoi(value);
  require(limit>=0&&limit<=10000,"budget","Invalid deployment call budget");int count=0;
  for(const auto &j:store_.list("job","",-1))if(j["data"].value("kind",std::string(""))!=""&&j["data"].value("kind",std::string(""))!="neon"&&j["data"].value("created_at",int64_t(0))>=now-86400)count+=j["data"].value("kind",std::string(""))=="copilot"||j["data"].value("kind",std::string(""))=="explanation"?2:1;
  require(count+(op=="turns"||p[0]=="copilot-explanations"?2:1)<=limit,"budget","Deployment model and tool request budget exhausted");
 }
 if(p[0]=="copilot-explanations") {
  if(method=="GET"&&op=="history"){auto r=scoped(a,id);require(r["type"]=="result","type","Select a saved result");Json items=Json::array();for(const auto&e:store_.list("explanation",r["case_id"],-1))if(e["data"]["packet"]["result_id"]==id)items.push_back(e);return {items};}
  if(method=="GET"){auto e=scoped(a,id);require(e["type"]=="explanation","type","Expected saved explanation");return {e};}
  require(method=="POST"&&id.empty(),"route","Unsupported explanation operation");keys(b,{"result_id","projection_id","profile_id","classification"},"");auto r=scoped(a,text(b,"result_id"));require(r["type"]=="result","type","Select a saved calculation");case_access(a,r["case_id"],true);
  Json pr;auto pid=b.value("projection_id",std::string());if(!pid.empty()){pr=scoped(a,pid);require(pr["type"]=="projection"&&pr["data"]["result_id"]==r["id"],"projection","Projection must belong to this exact calculation");}
  auto packet=explanation_packet(r,pr);auto profile_id=b.value("profile_id",std::string());
  if(profile_id.empty()){auto data=explanation_fallback(packet);data["packet"]=packet;data["created_at"]=now;data["author"]=a.id;data["model"]=nullptr;return {save(a,"explanation",r["case_id"],data),201};}
  require(!disabled,"disabled","Copilot disabled. Use the deterministic explanation");auto profile=store_.get(profile_id);require(profile["type"]=="copilot_profile","profile","Choose a model connection");auto data=profile["data"];
  require(data.value("enabled",false)&&data.value("health",std::string())=="capability_passed","profile_unqualified","Test and enable the connection first");require(data["provider"]!="mcp"||data.contains("model_tool"),"model_connection","Choose a model connection");auto classification=b.value("classification",std::string("corporate"));require(classification=="public"||classification=="corporate","classification","Choose public or corporate");require(classification=="public"||data["data_policy"]=="corporate","data_policy","This connection is not approved for corporate data");
  for(const auto&j:store_.list("job",r["case_id"],-1))if(j["data"].value("kind",std::string())=="explanation")require(j["data"]["state"]!="queued"&&j["data"]["state"]!="running","busy","An explanation is already being prepared");
  data.erase("health");data.erase("tested_job");data.erase("health_details");
  return {save(a,"job",r["case_id"],{{"kind","explanation"},{"attempt",0},{"packet",packet},{"context",{{"explanation_contract","1.0"},{"packet",packet}}},{"profile",data},{"profile_id",profile_id},{"profile_version",profile["version"]},{"state","queued"},{"actor",a.id},{"created_at",now}}),202};
 }
 if(p[0]=="copilot-capabilities")return {{{"schema_version","2.0"},{"fact_schema",fact_schema()},{"fact_definitions",fact_definitions()},{"architecture_library",library},{"disabled",disabled},{"fields",copilot_fields()},{"output_schema",copilot_schema()},{"manual_available",true},{"provider_qualification","Per-profile capability test required. Live interpretation qualification is separate"}}};
 if(p[0]=="copilot-profiles") {
  if(method=="GET"&&id.empty()){Json profiles=Json::array();for(auto r:store_.list("copilot_profile"))profiles.push_back(public_profile(r));return {profiles};}
  require(a.role=="admin","forbidden","Administrator required for model and MCP connections");
  if(method=="POST"&&id.empty()){validate_model_profile(b);auto data=b;data["health"]="untested";return {save(a,"copilot_profile","",data),201};}
  auto profile=store_.get(id);require(profile["type"]=="copilot_profile","type","Expected connection profile");
  if(method=="POST"&&op=="disable"){auto data=profile["data"];data["enabled"]=false;data["health"]="disabled";store_.audit(a.id,"disable_copilot_profile","",{{"profile_id",id}});return {store_.update(id,profile["version"],data)};}
  if(method=="POST"&&op=="test") {
   require(!disabled,"disabled","Copilot is disabled by the deployment administrator");auto data=profile["data"];data.erase("health");data.erase("tested_job");
   auto job=save(a,"job","",{{"kind",data["provider"]=="mcp"&&!data.contains("model_tool")?"mcp_test":"copilot_test"},{"profile_id",id},{"profile_version",profile["version"]},{"profile",data},{"context",{{"task","Connection test. Return question Ready and an empty changes array."}}},{"state","queued"},{"created_at",now},{"actor",a.id},{"attempt",0}});return {job,202};
  }
 }
 if(p[0]=="copilot-sessions") {
  if(method=="POST"&&id.empty()){
   keys(b,{"case_id","draft_id","classification","profile_id"},"");auto c=case_access(a,text(b,"case_id"),true);
   Json input=copilot_empty(c["data"]["name"]);std::string did;int dv=0;
   if(b.contains("draft_id")&&!text(b,"draft_id").empty()){auto d=scoped(a,text(b,"draft_id"));require(d["type"]=="draft"&&d["case_id"]==c["id"],"draft","Draft belongs to another case");auto compatibility=assisted_review(d["data"],catalog);require(compatibility.value("can_copy",false),"assisted_unavailable",compatibility["message"]);input=assisted_input(d["data"]);did=d["id"];dv=d["version"];}
   auto classification=b.value("classification",std::string("corporate"));require(classification=="corporate"||classification=="public","classification","Invalid classification");
   return {save(a,"copilot_session",c["id"],{{"input",input},{"revision",1},{"draft_id",did},{"draft_version",dv},{"classification",classification},{"profile_id",b.value("profile_id",std::string(""))},{"turns",0},{"state","open"},{"author",a.id}}),201};
  }
  auto session=scoped(a,id);require(session["type"]=="copilot_session","type","Expected assistant session");
  if(method=="GET"&&op.empty())return {session};
  auto sources=[&](){Json out=Json::array();for(auto r:store_.list("copilot_source",session["case_id"],-1))if(r["data"]["session_id"]==id)out.push_back(r);return out;};
  if(method=="GET"&&op=="history"){Json out={{"sources",sources()},{"proposals",Json::array()},{"jobs",Json::array()}};for(auto r:store_.list("copilot_proposal",session["case_id"],-1))if(r["data"]["session_id"]==id)out["proposals"].push_back(r);for(auto r:store_.list("job",session["case_id"],-1))if(r["data"].value("session_id",std::string(""))==id){auto clean=r;clean["data"].erase("context");clean["data"].erase("profile");out["jobs"].push_back(clean);}return {out};}
  case_access(a,session["case_id"],true);
  if(method=="POST"&&op=="fork") {
   keys(b,{"name"},"");auto name=text(b,"name");require(!name.empty()&&name.size()<=240,"name","Name the scenario variant");
   auto c=save(a,"case","",{{"name",name},{"owner",a.id},{"members",Json::array()},{"archived",false}});
   auto sd=session["data"];sd["input"]["name"]=name;sd["draft_id"]="";sd["draft_version"]=0;sd["turns"]=0;sd["revision"]=1;sd["baseline_session_id"]=id;
   return {save(a,"copilot_session",c["id"],sd),201};
  }
  if(method=="POST"&&op=="sources") {
   keys(b,{"name","text","kind"},"");auto content=text(b,"text"),kind=text(b,"kind");require(kind=="message"||kind=="document"||kind=="telemetry","kind","Use message, document or telemetry");require(!content.empty()&&content.size()<=32000,"source_limit","Source text must contain 1 to 32000 bytes");require(sources().size()<32,"source_limit","Session source limit reached");
   auto name=text(b,"name");require(!name.empty()&&name.size()<=160,"name","Source name must contain 1 to 160 characters");
   return {save(a,"copilot_source",session["case_id"],{{"session_id",id},{"text",content},{"name",name},{"kind",kind},{"digest",digest(content)},{"author",a.id}}),201};
  }
  if(method=="POST"&&op=="proposals") {
   if(a.role=="agent") {auto c=case_access(a,session["case_id"]);int used=0;for(auto r:store_.list("copilot_proposal",session["case_id"],-1))if(r["data"].value("author",std::string(""))==a.id)++used;require(used<c["data"].value("agent_proposal_limit",0),"agent_budget","No remaining authorized proposals");}
   auto proposal=b.contains("facts")?fact_proposal(b,session["data"],sources(),catalog,library):copilot_proposal(b,session["data"],sources(),catalog);proposal["session_id"]=id;proposal["author"]=a.id;
   return {save(a,"copilot_proposal",session["case_id"],proposal),201};
  }
  if(method=="POST"&&op=="turns") {
   keys(b,{"profile_id","activation_id"},"");require(!disabled,"disabled","Copilot disabled. Continue using the workload builder");auto profile=store_.get(text(b,"profile_id"));require(profile["type"]=="copilot_profile","profile","Invalid model profile");
   auto data=profile["data"];require(data.value("health","")=="capability_passed"&&data.value("enabled",false),"profile_unqualified","Test and enable this connection first");
   require(data["provider"]!="mcp"||data.contains("model_tool"),"model_connection","Select a model connection, not a knowledge-only MCP server");
   require(session["data"]["classification"]=="public"||data["data_policy"]=="corporate","data_policy","Corporate case data cannot be sent to this profile");
   require(session["data"]["turns"].get<int>()<data["max_turns"].get<int>(),"budget","Session turn budget exhausted. Continue manually");
   for(auto j:store_.list("job",session["case_id"],-1))if(j["data"].value("session_id",std::string(""))==id)require(j["data"]["state"]!="queued"&&j["data"]["state"]!="running"&&j["data"]["state"]!="cancel_requested","busy","Wait for or cancel the current turn");
   auto src=sources();Json context={{"accepted_input",session["data"]["input"]},{"sources",src},{"fact_contract","2.0"},{"fact_definitions",fact_definitions()},{"architecture_library",library},{"accepted_facts",session["data"].value("facts",Json::array())}};
   if(b.contains("activation_id")&&!text(b,"activation_id").empty()) {
    auto activation=scoped(a,text(b,"activation_id"));require(activation["type"]=="activation"&&!activation["data"]["withdrawn"].get<bool>(),"activation","Selected knowledge activation is unavailable");
    context["selected_knowledge"]={{"activation_id",activation["id"]},{"pack_digest",activation["data"]["pack_digest"]},{"channel",activation["data"]["channel"]},{"resolved",activation["data"]["knowledge_lock"]["resolved"]}};
   }
   Json recent=Json::array();for(auto r:store_.list("copilot_proposal",session["case_id"],-1))if(r["data"]["session_id"]==id&&recent.size()<3)recent.push_back({{"question",r["data"]["question"]},{"state",r["data"]["state"]}});context["recent_review_status"]=recent;
   require(context.dump().size()<120000,"context_budget","Source context exceeds budget. Start a focused session");data.erase("health");data.erase("tested_job");
   auto job=save(a,"job",session["case_id"],{{"kind","copilot"},{"session_id",id},{"base_revision",session["data"]["revision"]},{"session_snapshot",session["data"]},{"sources",src},{"catalog",catalog},{"context",context},{"profile",data},{"profile_id",profile["id"]},{"profile_version",profile["version"]},{"prompt_version","facts-2.0"},{"prompt_digest",digest(fact_prompt())},{"adapter_version","1.0"},{"state","queued"},{"created_at",now},{"actor",a.id},{"attempt",0}});
   auto sd=session["data"];sd["turns"]=sd["turns"].get<int>()+1;sd["profile_id"]=profile["id"];store_.update(id,session["version"],sd);return {job,202};
  }
  if(method=="POST"&&op=="mcp-import") {
   keys(b,{"profile_id","tool","arguments"},"");require(!disabled,"disabled","Copilot disabled");auto profile=store_.get(text(b,"profile_id"));require(profile["type"]=="copilot_profile"&&profile["data"]["provider"]=="mcp","profile","Expected MCP profile");auto data=profile["data"];
   require(data.value("health","")=="capability_passed"&&data.value("enabled",false),"profile_unqualified","Test the MCP connection first");require(session["data"]["classification"]=="public"||data["data_policy"]=="corporate","data_policy","Case data is not permitted for this destination");
   bool allowed=false;for(const auto&t:data.value("tools",Json::array()))if(t["name"]==text(b,"tool")&&t.value("read_only",false))allowed=true;
   require(allowed,"mcp_scope","Only explicitly approved read-only tools may supply case context");require(b.at("arguments").is_object()&&b["arguments"].dump().size()<=16000,"arguments","Arguments must be a bounded object");require(sources().size()<32,"source_limit","Session source limit reached");
   data.erase("health");data.erase("tested_job");return {save(a,"job",session["case_id"],{{"kind","mcp_import"},{"session_id",id},{"profile_id",profile["id"]},{"profile",data},{"tool",b["tool"]},{"arguments",b["arguments"]},{"state","queued"},{"created_at",now},{"actor",a.id},{"attempt",0}}),202};
  }
 }
 if(p[0]=="copilot-proposals") {
  auto proposal=scoped(a,id);require(proposal["type"]=="copilot_proposal","type","Expected proposal");if(method=="GET")return {proposal};
  require(a.role!="agent","forbidden","An agent cannot approve its own proposals");case_access(a,proposal["case_id"],true);require(proposal["data"]["state"]=="proposed","reviewed","Proposal has already been reviewed");
  auto session=scoped(a,proposal["data"]["session_id"]);auto sd=session["data"];
  if(method=="POST"&&op=="reject"){auto pd=proposal["data"];pd["state"]="rejected";pd["reviewer"]=a.id;return {store_.update(id,proposal["version"],pd)};}
  if(method=="POST"&&op=="apply") {
   keys(b,{"selected","accept_assumptions"},"");require(sd["revision"]==proposal["data"]["base_revision"],"stale_proposal","Inputs changed. Create and review a new proposal");
   require(b.at("selected").is_array()&&!b["selected"].empty(),"selection","Choose at least one proposed change");require(b.value("accept_assumptions",false),"acceptance","Review and accept the planning assumptions before applying");
   if(proposal["data"].contains("facts"))require(b["selected"].size()==proposal["data"]["changes"].size(),"fact_review","Review the fact ledger and its translated changes together");
   Json input=sd["input"],selected=Json::array();if(!input.contains("input_basis"))input["input_basis"]=Json::object();std::set<size_t> seen;
   for(auto index:b["selected"]){require(index.is_number_unsigned()||index.is_number_integer(),"selection","Expected integer index");int n=index.get<int>();require(n>=0&&static_cast<size_t>(n)<proposal["data"]["changes"].size()&&seen.insert(static_cast<size_t>(n)).second,"selection","Invalid or duplicate selection");auto row=proposal["data"]["changes"][n];input[Json::json_pointer(text(row,"path"))]=row["value"];if(row["field"]=="components")input["input_basis"]=Json::object();input["input_basis"][text(row,"field")]=Json{{"basis",row["basis"]},{"source_id",row["source_id"]}};selected.push_back(row);}
   if(proposal["data"].contains("facts")){
    const std::map<std::string,std::vector<std::string>> sources_by_field={{"rate",{"requests_peak","requests"}},{"users",{"active_users"}},{"interval",{"requests_per_user"}},{"calls",{"calls_selected","calls_upper","calls_typical"}},{"input_tokens",{"input_tokens"}},{"output_tokens",{"output_tokens"}},{"model",{"model"}},{"tokens",{"training_tokens"}},{"days",{"deadline"}},{"jobs",{"jobs"}},{"window",{"window","window_start"}}};
    for(size_t i=0;i<input["components"].size();++i)for(const auto &[field,concepts]:sources_by_field){
     if(!input["components"][i].contains(field))continue;
     for(const auto &kind:concepts){bool found=false;for(const auto &f:proposal["data"]["facts"])if(f["activity"]==input["components"][i]["name"]&&f["concept"]==kind&&f["status"]!="unknown"){
      input["input_basis"]["components."+std::to_string(i)+"."+field]={{"basis",f["status"]=="assumed"?"planning_assumption":"customer_statement"},{"source_id",f["source_id"]}};found=true;break;
     }if(found)break;}
    }
   }
   input["accepted"]=true;copilot_validate_input(input,catalog);Json draft;
   if(!input["components"].empty()){auto workload=guided_workload(input,catalog);
   if(sd["draft_id"]!=""){auto current=store_.get(sd["draft_id"]);require(current["version"]==sd["draft_version"],"stale_draft","Draft was edited outside the copilot. Start a fresh session");workload=assisted_merge(current["data"],workload,catalog);draft=store_.update(current["id"],current["version"],workload);}
   else draft=save(a,"draft",session["case_id"],workload);
   } else draft={{"id",""},{"version",0},{"data",Json::object()}};
   if(proposal["data"].contains("facts")){sd["facts"]=proposal["data"]["facts"];sd["fact_contract"]="2.0";sd["knowledge_version"]=proposal["data"]["knowledge_version"];sd["knowledge_digest"]=proposal["data"]["knowledge_digest"];sd["next_question"]=proposal["data"]["question"];sd["ready_for_estimate"]=proposal["data"]["ready_for_estimate"];}
   auto review=save(a,"copilot_review",session["case_id"],{{"proposal_id",id},{"selected",selected},{"reviewer",a.id},{"draft_id",draft["id"]},{"draft_version",draft["version"]},{"input_digest",digest(input)}});
   sd["input"]=input;sd["revision"]=sd["revision"].get<int>()+1;sd["draft_id"]=draft["id"];sd["draft_version"]=draft["version"];auto updated=store_.update(session["id"],session["version"],sd);
   auto pd=proposal["data"];pd["state"]="applied";pd["review_id"]=review["id"];store_.update(id,proposal["version"],pd);
   return {{{"session",updated},{"draft",draft},{"review",review},{"case_id",session["case_id"]}},201};
  }
 }
 if(p[0]=="copilot-context"&&method=="GET"){
  auto c=case_access(a,id);return {{{"case",c},{"sessions",store_.list("copilot_session",id)},{"catalog",catalog},{"catalog_digest",digest(catalog)},{"architecture_library",library},{"fact_schema",fact_schema()},{"fact_definitions",fact_definitions()}}};
 }
 if(p[0]=="copilot-facts"&&method=="GET"){
  auto result=scoped(a,id);require(result["type"]=="result","result","Expected compilation result");auto r=result["data"]["result"];auto revision=scoped(a,result["data"]["revision_id"]);auto draft=scoped(a,revision["data"]["source_draft"]);bool stale=draft["version"]!=revision["data"]["source_version"];
  return {{{"result_id",id},{"source_draft_id",revision["data"]["source_draft"]},{"revision_id",result["data"]["revision_id"]},{"result_digest",digest(r)},{"stale",stale},{"planning",r.value("planning",Json::object())},{"facts",r.value("facts",Json::array())},{"questions",r.value("questions",Json::array())},{"source","Deterministic engine. No model-generated numerical claims"}}};
 }
 throw Error("route","Unknown copilot operation","",404);
}
}
