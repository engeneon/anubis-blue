#include "application/copilot/explanation.hpp"
#include "adapters/model_transport.hpp"
#include "application/copilot/facts.hpp"
#include <httplib/httplib.h>
#include <regex>
#include <sstream>
#include <chrono>
#include <netdb.h>
#include <arpa/inet.h>
namespace anubis {
static bool explicit_origin(const std::string &origin) {
 const char* env=std::getenv("ANUBIS_AI_ALLOWED_ORIGINS");if(!env)return false;
 auto allowed=parse(env);require(allowed.is_array(),"endpoint_policy","Origin policy must be an array");
 return std::find(allowed.begin(),allowed.end(),origin)!=allowed.end();
}
void validate_model_profile(const Json &p) {
 keys(p,{"name","provider","origin","path","model","secret_env","enabled","max_turns","max_output_tokens","data_policy","protocol","tools","model_tool","model_tool_digest","reasoning_effort"},"");
 auto provider=text(p,"provider"),origin=text(p,"origin");
 if(p.contains("reasoning_effort"))require(provider=="deepseek"&&(p["reasoning_effort"]=="disabled"||p["reasoning_effort"]=="low"||p["reasoning_effort"]=="high"),"reasoning","DeepSeek reasoning must be disabled, low or high");
 require(std::set<std::string>{"openai","anthropic","deepseek","xai","gateway","mcp"}.contains(provider),"provider","Unsupported provider");
 require(std::regex_match(origin,std::regex("https?://[A-Za-z0-9.-]+(:[0-9]{1,5})?")),"endpoint","Origin must not include a path, credentials or query");
 const std::map<std::string,std::string> standard={{"openai","https://api.openai.com"},{"anthropic","https://api.anthropic.com"},{"deepseek","https://api.deepseek.com"},{"xai","https://api.x.ai"}};
 bool direct=standard.contains(provider)&&standard.at(provider)==origin;
 require(direct||explicit_origin(origin),"endpoint_policy","Corporate and private origins require server-side ANUBIS_AI_ALLOWED_ORIGINS approval");
 require(origin.starts_with("https://")||(explicit_origin(origin)&&std::regex_match(origin,std::regex("http://127\\.0\\.0\\.1:[0-9]{4,5}"))),"tls","TLS required except explicitly allowed loopback test services");
 require(std::regex_match(text(p,"path"),std::regex("/[A-Za-z0-9_./-]+"))&&text(p,"path").find("..") == std::string::npos,"path","Invalid endpoint path");
 require(std::regex_match(text(p,"secret_env"),std::regex("ANUBIS_AI_KEY_[A-Z0-9_]+")),"secret_reference","Use an ANUBIS_AI_KEY_ prefixed environment variable reference");
 require(p.at("enabled").is_boolean(),"enabled","Enabled must be boolean");
 require(p.at("max_turns").is_number_integer()&&p["max_turns"]>=1&&p["max_turns"]<=100,"budget","Turn limit must be 1 to 100");
 require(p.at("max_output_tokens").is_number_integer()&&p["max_output_tokens"]>=256&&p["max_output_tokens"]<=8192,"budget","Output token limit must be 256 to 8192");
 require(text(p,"name").size()<=120&&!text(p,"name").empty()&&text(p,"model").size()<=160,"profile","Invalid profile name or model");
 require(text(p,"data_policy")=="public"||text(p,"data_policy")=="corporate","policy","Choose public or corporate data policy");
}
static httplib::Headers auth(const Json &p) {
 auto env=text(p,"secret_env");const char* secret=std::getenv(env.c_str());require(secret&&std::string(secret).size()>=8,"credentials_missing","Backend API credential is not configured");
 httplib::Headers h={{"Accept","application/json"}};
 if(p["provider"]=="anthropic"){h.emplace("x-api-key",secret);h.emplace("anthropic-version","2023-06-01");}
 else h.emplace("Authorization",std::string("Bearer ")+secret);
 return h;
}
static Json post(const Json &p,const Json &body,httplib::Headers &headers,bool notification=false) {
 validate_model_profile(p);require(p["enabled"].get<bool>(),"disabled","Connection is disabled");
 auto origin=text(p,"origin");httplib::Client client(origin);client.set_connection_timeout(5);client.set_read_timeout(120);client.set_write_timeout(10);client.set_follow_location(false);client.enable_server_certificate_verification(true);
 // Pin a resolved public IPv4 address for standard providers. Private gateways require explicit deployment approval.
 if(!explicit_origin(origin)){
  auto host=origin.substr(origin.find("://")+3);addrinfo hints{},*res=nullptr;hints.ai_family=AF_INET;hints.ai_socktype=SOCK_STREAM;
  require(getaddrinfo(host.c_str(),nullptr,&hints,&res)==0,"provider_unavailable","Provider DNS lookup failed");std::string ip;
  for(auto r=res;r;r=r->ai_next){auto a=ntohl(reinterpret_cast<sockaddr_in*>(r->ai_addr)->sin_addr.s_addr);auto first=a>>24,second=(a>>16)&255;
   if(first==0||first==10||first==127||first>=224||(first==169&&second==254)||(first==172&&second>=16&&second<=31)||(first==192&&second==168)||(first==100&&second>=64&&second<=127))continue;
   char value[INET_ADDRSTRLEN];inet_ntop(AF_INET,&reinterpret_cast<sockaddr_in*>(r->ai_addr)->sin_addr,value,sizeof(value));ip=value;break;}
  freeaddrinfo(res);require(!ip.empty(),"endpoint_policy","Provider resolved to a disallowed address");client.set_hostname_addr_map({{host,ip}});
 }
 auto started=std::chrono::steady_clock::now();
 auto response=client.Post(text(p,"path"),headers,body.dump(),"application/json",[&](uint64_t current,uint64_t total){return current<=512*1024 && total<=512*1024 && std::chrono::steady_clock::now()-started<std::chrono::seconds(60);});
 require(bool(response),"provider_unavailable","Connection failed or timed out. Continue manually or retry explicitly");
 if(response->status==402)throw Error("provider_billing","The provider reports insufficient account balance. Fund the account or select another approved connection");
 if(response->status==401||response->status==403)throw Error("provider_authentication","The provider rejected authentication or account access. Check the backend credential and model permission");
 if(response->status==429)throw Error("provider_rate_limit","The provider request limit was reached. Retry later or continue manually");
 require(response->status>=200&&response->status<300,"provider_rejected","Provider rejected the request with HTTP "+std::to_string(response->status)+". Check the connection profile");
 require(response->body.size()<=512*1024,"response_limit","Provider response exceeds limit");
 auto sid=response->get_header_value("Mcp-Session-Id");if(!sid.empty())headers.emplace("Mcp-Session-Id",sid);
 if(notification&&response->body.empty())return Json::object();
 auto raw=response->body;
 if(raw.starts_with("event:")||raw.starts_with("data:")) {
  std::stringstream ss(raw);std::string line;Json result;
  while(std::getline(ss,line))if(line.starts_with("data:")){try{auto candidate=parse(line.substr(5));if(candidate.contains("id")&&candidate["id"]==body.value("id",Json()))result=candidate;}catch(...) {}}
  require(!result.is_null(),"mcp_response","No matching JSON-RPC response");return result;
 }
 return parse(raw);
}
// Deliberately bounded JSON Schema subset for approved read-only MCP inputs.
static void validate_tool_arguments(const Json &schema,const Json &value,int depth=0) {
 require(depth<=12&&schema.is_object(),"mcp_schema","Unsupported tool schema");
 const std::set<std::string> supported={"type","properties","required","additionalProperties","items","enum","minimum","maximum","minLength","maxLength","minItems","maxItems","description","title","default","$schema"};
 for(auto it=schema.begin();it!=schema.end();++it)require(supported.contains(it.key()),"mcp_schema","Tool schema uses an unsupported validation keyword");
 auto type=text(schema,"type");
 bool valid=(type=="object"&&value.is_object())||(type=="array"&&value.is_array())||(type=="string"&&value.is_string())||(type=="number"&&value.is_number())||(type=="integer"&&value.is_number_integer())||(type=="boolean"&&value.is_boolean())||(type=="null"&&value.is_null());require(valid,"mcp_arguments","Tool argument type mismatch");
 if(schema.contains("enum"))require(std::find(schema["enum"].begin(),schema["enum"].end(),value)!=schema["enum"].end(),"mcp_arguments","Tool enum value is invalid");
 if(value.is_object()){auto props=schema.value("properties",Json::object());for(auto r:schema.value("required",Json::array()))require(value.contains(r.get<std::string>()),"mcp_arguments","Required tool field missing");for(auto it=value.begin();it!=value.end();++it){require(props.contains(it.key()),"mcp_arguments","Unknown tool field");validate_tool_arguments(props[it.key()],it.value(),depth+1);}}
 if(value.is_array()){require(value.size()>=schema.value("minItems",size_t(0))&&value.size()<=schema.value("maxItems",size_t(100)),"mcp_arguments","Tool array exceeds bounds");for(const auto &v:value)validate_tool_arguments(schema.at("items"),v,depth+1);}
 if(value.is_string())require(value.get<std::string>().size()>=schema.value("minLength",size_t(0))&&value.get<std::string>().size()<=schema.value("maxLength",size_t(16000)),"mcp_arguments","Tool string exceeds bounds");
 if(value.is_number()){if(schema.contains("minimum"))require(value.get<double>()>=schema["minimum"].get<double>(),"mcp_arguments","Tool number below minimum");if(schema.contains("maximum"))require(value.get<double>()<=schema["maximum"].get<double>(),"mcp_arguments","Tool number above maximum");}
}
Json execute_mcp(const Json &p,const std::string &name,const Json &args) {
 require(p["provider"]=="mcp","mcp","Expected MCP connection");auto h=auth(p);h.erase("Accept");h.emplace("Accept","application/json, text/event-stream");
 auto version=p.value("protocol",std::string("2025-06-18"));require(version=="2025-06-18","mcp_version","Only the tested MCP protocol version is supported");
 auto init=post(p,{{"jsonrpc","2.0"},{"id",1},{"method","initialize"},{"params",{{"protocolVersion",version},{"capabilities",Json::object()},{"clientInfo",{{"name","anubis"},{"version","1.0"}}}}}},h);
 require(init.contains("result")&&init["result"].value("protocolVersion","")==version,"mcp_version","MCP protocol negotiation failed");h.emplace("MCP-Protocol-Version",version);
 post(p,{{"jsonrpc","2.0"},{"method","notifications/initialized"}},h,true);
 auto list=post(p,{{"jsonrpc","2.0"},{"id",2},{"method","tools/list"}},h);
 require(list.contains("result")&&list["result"].contains("tools"),"mcp_tools","Tool discovery failed");
 if(name.empty())return list["result"];
 std::string approved;for(const auto&t:p.value("tools",Json::array()))if(t["name"]==name)approved=text(t,"schema_digest");
 if(p.value("model_tool",std::string(""))==name)approved=p.value("model_tool_digest",std::string(""));
 require(!approved.empty(),"mcp_scope","Tool is not approved");bool match=false;
 for(const auto&t:list["result"]["tools"])if(t["name"]==name&&digest(t["inputSchema"])==approved){validate_tool_arguments(t["inputSchema"],args);match=true;}
 require(match,"mcp_schema_changed","Tool schema changed. Administrator review required");
 auto r=post(p,{{"jsonrpc","2.0"},{"id",3},{"method","tools/call"},{"params",{{"name",name},{"arguments",args}}}},h);
 require(r.contains("result")&&!r["result"].value("isError",false),"mcp_tool_failed","MCP tool failed");return r["result"];
}
Json execute_model(const Json &p,const Json &context) {
 bool explain=context.contains("explanation_contract"),fact_mode=context.contains("fact_contract");auto schema=explain?explanation_schema():fact_mode?fact_schema():copilot_schema();auto instructions=(explain?explanation_prompt():fact_mode?fact_prompt():copilot_prompt())+"\nOutput schema: "+schema.dump();Json body,result;auto provider=text(p,"provider");
 require(context.dump().size()<120000,"context_budget","Context exceeds the allowed input budget");
 if(provider=="mcp") {
  result=execute_mcp(p,text(p,"model_tool"),{{"instructions",instructions},{"context",context},{"max_output_tokens",p["max_output_tokens"]}});
  if(result.contains("structuredContent"))return {{"output",result["structuredContent"]},{"usage",Json::object()},{"provider_request_id",""}};
  require(result.contains("content")&&!result["content"].empty(),"provider_output","Missing structured model response");return {{"output",parse(text(result["content"][0],"text"))},{"usage",Json::object()},{"provider_request_id",""}};
 }
 auto messages=Json::array({{{"role","user"},{"content",context.dump()}}});
 if(provider=="anthropic")body={{"model",p["model"]},{"max_tokens",p["max_output_tokens"]},{"system",instructions},{"messages",messages},{"tools",Json::array({{{"name","propose_workload"},{"description","Propose workload inputs for review"},{"input_schema",schema}}})},{"tool_choice",{{"type","tool"},{"name","propose_workload"}}}};
 else {messages.insert(messages.begin(),Json{{"role","system"},{"content",instructions}});body={{"model",p["model"]},{"messages",messages},{"response_format",{{"type","json_object"}}}};body[provider=="openai"?"max_completion_tokens":"max_tokens"]=p["max_output_tokens"];}
 if(provider=="deepseek"){auto effort=p.value("reasoning_effort",std::string("disabled"));body["thinking"]={{"type",effort=="disabled"?"disabled":"enabled"}};if(effort!="disabled")body["reasoning_effort"]=effort;}
 auto h=auth(p);result=post(p,body,h);Json output;
 if(provider=="anthropic") {require(result.value("stop_reason","")!="max_tokens","truncated","Model response was truncated");for(const auto &c:result.at("content"))if(c.value("type","")=="tool_use"&&c.value("name","")=="propose_workload")output=c.at("input");}
 else {auto choice=result.at("choices").at(0);require(choice.value("finish_reason","")=="stop","provider_output","Model response was incomplete or refused");output=parse(text(choice.at("message"),"content"));}
 require(output.is_object(),"provider_output","Model did not return a proposal object");
 return {{"output",output},{"usage",result.value("usage",Json::object())},{"provider_request_id",result.value("id",std::string(""))},{"adapter_version","1.0"},{"prompt_version",fact_mode?"facts-2.0":"copilot-1.1"}};
}
}
