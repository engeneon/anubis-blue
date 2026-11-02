#include "application/characterization/closure.hpp"
#include "application/characterization/assisted.hpp"
#include "application/characterization/resolve.hpp"
#include "application/characterization/guided.hpp"
#include "application/service.hpp"
#include "application/copilot/facts.hpp"
#include "adapters/model_transport.hpp"
#include "adapters/neon_transport.hpp"
#include "application/intake/import.hpp"
#include "application/knowledge/resolve.hpp"
#include "compiler/planning.hpp"
#include "compiler/qualification.hpp"
#include <filesystem>
#include <fstream>
#include <openssl/rand.h>
#include <set>
#include <sstream>
namespace anubis {
std::string new_id(const std::string &p) {
  unsigned char b[16];
  if (RAND_bytes(b, 16) != 1)
    throw std::runtime_error("Random source unavailable");
  std::string s = p + "_";
  for (auto c : b) {
    s += "0123456789abcdef"[c >> 4];
    s += "0123456789abcdef"[c & 15];
  }
  return s;
}
static Json read_json(const std::string &p) {
  std::ifstream f(p);
  require(bool(f), "file", "Artifact unavailable");
  std::stringstream ss;
  ss << f.rdbuf();
  return parse(ss.str());
}
Service::Service(const std::string &database, const std::string &root)
    : store_(database), root_(root), database_(database) {
  if (!store_.shared())
    for (auto j : store_.list("job", "", -1)) {
      auto d = j["data"];
      if (d["state"] == "running" || d["state"] == "cancel_requested") {
        d["state"] = d.value("kind", "compile") != "compile" ? "outcome_unknown"
                     : d["state"] == "cancel_requested"   ? "cancelled"
                                                          : "queued";
        d["recovery"] = "Recovered after exclusive local service restart";
        store_.update(j["id"], j["version"], d);
      }
    }
  worker_ = std::thread([this] { work(); });
}
Service::~Service() {
  {
    std::lock_guard guard(mutex_);
    stopping_ = true;
  }
  wake_.notify_all();
  worker_.join();
}
Json Service::case_access(const Actor &a, const std::string &id, bool write) {
  auto c = store_.get(id);
  require(c["type"] == "case", "type", "Expected case");
  bool member = c["data"]["owner"] == a.id;
  for (auto m : c["data"].value("members", Json::array()))
    if (m == a.id)
      member = true;
  if (!member)
    throw Error("forbidden", "Case access denied", "", 403);
  require(!write||!c["data"].value("deleted",false),"deleted_engagement","Restore this engagement from Trash before changing it");
  if (write && a.role == "viewer")
    throw Error("forbidden", "Read-only identity", "", 403);
  return c;
}
Json Service::scoped(const Actor &a, const std::string &id) {
  auto r = store_.get(id);
  if (r["case_id"] != "")
    case_access(a, r["case_id"]);
  else
    require(r["type"] == "pack" || r["type"] == "activation" ||
                r["type"] == "qualification_protocol" || r["type"] == "qualification_report" ||
                a.role == "admin",
            "forbidden", "Global record restricted");
  return r;
}
Json Service::save(const Actor &a, const std::string &type, const std::string &cid,
                   const Json &body) {
  auto r = store_.put(type, new_id(type), cid, body);
  store_.audit(a.id, "create_" + type, cid, {{"id", r["id"]}, {"digest", digest(body)}});
  return r;
}
Reply Service::request(const Actor &a, const std::string &method, const std::string &path,
                       const Json &b, const std::string &match, const std::string &idem) {
  std::unique_lock lock(mutex_);
  std::vector<std::string> parts;
  std::stringstream ss(path.substr(8));
  std::string s;
  while (std::getline(ss, s, '/'))
    if (!s.empty())
      parts.push_back(s);
  require(!parts.empty(), "route", "Route missing");
  bool mutation = method != "GET";
  if (mutation && a.role == "agent") {
    require(
        parts[0] == "characterizations" || parts[0] == "compilations" || parts[0] == "comparisons" ||
            parts[0] == "observation-proposals" || (parts[0] == "copilot-sessions" && parts.size()==3 && parts[2]=="proposals"),
        "agent_scope",
        "Agent identity may propose observations, compile frozen inputs and compare results only");
  }

  if (mutation && a.role == "viewer")
    throw Error("forbidden", "Read-only identity", "", 403);
  auto key = "idem_" + digest(Json::array({a.id, method, path, idem}));
  if (method == "POST" && path == "/api/v1/admin/backup") {
    require(a.role == "admin", "forbidden", "Administrator required");
    if (store_.shared())
      throw Error("backup_profile", "Use PostgreSQL snapshot tooling for the shared profile", "",
                  409);
    auto id = new_id("backup");
    auto dir = std::filesystem::path(database_).parent_path() / "backups";
    std::filesystem::create_directories(dir);
    auto destination = (dir / (id + ".sqlite")).string();
    store_.backup(destination);
    auto manifest =
        save(a, "backup", "",
             {{"path", destination}, {"profile", "sqlite-local-v1"}, {"external_blobs", false}});
    return {manifest, 201};
  }
  if (mutation)
    store_.begin();
  try {
    if (mutation && !idem.empty()) {
      try {
        auto old = store_.get(key)["data"];
        if (old["request_digest"] != digest(b))
          throw Error("idempotency_conflict", "Key reused with different payload", "", 409);
        if (old.contains("case_id") && old["case_id"] != "")
          case_access(a, old["case_id"]);
        store_.commit();
        return {old["reply"], old["status"]};
      } catch (const Error &e) {
        if (e.status != 404)
          throw;
      }
    }
    auto reply = dispatch(a, method, parts, b, match);
    if (mutation && !idem.empty()) {
      std::string cid = reply.body.value("case_id", "");
      store_.put("idempotency", key, cid,
                 {{"request_digest", digest(b)},
                  {"reply", reply.body},
                  {"status", reply.status},
                  {"case_id", cid}});
    }
    if (mutation)
      store_.commit();
    wake_.notify_all();
    return reply;
  } catch (...) {
    if (mutation)
      store_.rollback();
    throw;
  }
}
static int64_t expected(const std::string &match) {
  if (match.empty())
    throw Error("precondition_required", "If-Match version header required", "", 428);
  try {
    size_t n;
    auto v = std::stoll(match, &n);
    require(n == match.size() && v > 0, "version", "Invalid expected version");
    return v;
  } catch (const Error &) {
    throw;
  } catch (...) {
    throw Error("version", "Invalid expected version");
  }
}
Reply Service::dispatch(const Actor &a, const std::string &method,
                        const std::vector<std::string> &p, const Json &b,
                        const std::string &match) {
  if(p[0].starts_with("copilot-")) return copilot_dispatch(a,method,p,b,match);
  auto top = p[0];
  auto id = p.size() > 1 ? p[1] : "";
  auto op = p.size() > 2 ? p[2] : "";
  if (method == "GET" && top == "openapi")
    return {read_json(root_ + "/contracts/openapi.json")};
  if (method == "GET" && top == "capabilities")
    return {capabilities()};
  if (method == "GET" && top == "integration-capabilities") {
    try {
      return {
          {{"neon", neon_target()}, {"submission_enabled", true}, {"production_qualified", false}}};
    } catch (const Error &) {
      return {{{"submission_enabled", false}, {"mode", "manual"}, {"production_qualified", false}}};
    }
  }
  if (method == "GET" && top == "component-descriptors")
    return {component_descriptors()};
  if (method == "GET" && top == "me")
    return {{{"id", a.id}, {"role", a.role}}};
  if (method == "GET" && top == "guided-catalog") return {read_json(root_ + "/knowledge/guided-intake.json")};
  if (method == "POST" && top == "assisted-compatibility") return {assisted_review(b,read_json(root_ + "/knowledge/guided-intake.json"))};
  if (method == "POST" && top == "guided-workloads") return {guided_workload(b,read_json(root_ + "/knowledge/guided-intake.json"))};
  if (method == "GET" && top == "architecture-core") return {read_json(root_ + "/knowledge/architecture-core.json")};
  if (method == "POST" && top == "characterizations") return {characterize(b, read_json(root_ + "/knowledge/architecture-core.json"))};
  if (method == "GET" && top == "planning-catalog") return {planning_catalog()};
  if (method == "GET" && top == "stories") {
    Json stories = Json::array();
    for (auto n : {"meridian", "harbor", "aster", "synthetic", "meridian-planning", "harbor-planning", "aster-planning"})
      stories.push_back(read_json(root_ + "/tests/fixtures/" + n + ".json"));
    return {stories};
  }
  if (top == "cases") {
    if (method == "POST" && id.empty()) {
      keys(b, {"name"}, "");
      auto name = text(b, "name");
      require(!name.empty() && name.size() <= 240, "name", "Case name length 1–240");
      return {
          save(a, "case", "",
               {{"name", name}, {"owner", a.id}, {"members", Json::array()}, {"archived", false}}),
          201};
    }
    if (method == "GET" && (id.empty()||id=="trash")) {
      Json visible = Json::array();
      for (auto c : store_.list("case")) {
        if(c["data"].value("deleted",false)!=(id=="trash"))continue;
        if (c["data"]["owner"] == a.id ||
            std::find(c["data"]["members"].begin(), c["data"]["members"].end(), a.id) !=
                c["data"]["members"].end())
        {
          auto ds=store_.list("draft",c["id"]),rs=store_.list("result",c["id"]),ps=store_.list("projection",c["id"]);
          Json progress={{"phase",1},{"label","New engagement"},{"next_action","Describe the workload"},{"stale_result",false}};
          if(!store_.list("copilot_session",c["id"]).empty())progress={{"phase",2},{"label","Describing workload"},{"next_action","Review workload facts"},{"stale_result",false}};
          if(!ds.empty())progress={{"phase",3},{"label","Workload saved · calculation pending"},{"next_action","Review inputs and calculate requirements"},{"stale_result",false}};
          if(!rs.empty()){
            auto rev=store_.get(rs[0]["data"]["revision_id"]);bool stale=ds.empty()||rev["data"]["source_draft"]!=ds[0]["id"]||rev["data"]["source_version"]!=ds[0]["version"];
            progress={{"phase",stale?3:4},{"label",stale?"Inputs changed · recalculate":"Calculated · handoff pending"},{"next_action",stale?"Recalculate current workload":"Prepare design handoff"},{"stale_result",stale}};
            if(!stale)for(const auto &pr:ps)if(pr["data"]["result_id"]==rs[0]["id"]){progress["label"]="Handoff prepared · delivery pending";progress["next_action"]="Review deliverables and complete engagement";break;}
          }
          if(c["data"].value("status",std::string(""))!="completed") {
            Json description=Json::object();
            if(!ds.empty()&&ds[0]["data"].contains("characterization"))description=ds[0]["data"]["characterization"].value("guided_input",Json::object());
            if(description.empty()){auto sessions=store_.list("copilot_session",c["id"]);if(!sessions.empty())description=sessions[0]["data"].value("input",Json::object());}
            bool specialist=false;for(const auto &component:description.value("components",Json::array()))if(std::set<std::string>{"stream","generation","adaptation","other"}.contains(component.value("pattern",std::string(""))))specialist=true;
            if(specialist){progress["label"]="Specialist scope · further evidence or status-report closure";progress["next_action"]="Review specialist requirements or conclude with a final status report";}
          }
          if(c["data"].value("status",std::string(""))=="completed")progress={{"phase",5},{"label",c["data"].value("completion_outcome",std::string(""))=="concluded_without_handoff"?"Closed · final status report":"Completed · requirements delivered"},{"next_action","Retrieve deliverables or reopen for revisions"},{"stale_result",false}};
          c["workflow"]=progress;visible.push_back(c);
        }
      }
      return {visible};
    }
    auto c = case_access(a, id, method != "GET" && op!="restore");
    if (method == "GET" && op.empty())
      return {c};
    if(method=="POST"&&(op=="delete"||op=="restore")) {
      keys(b,{"confirm"},"");require(c["data"]["owner"]==a.id&&a.role!="agent","forbidden","Only the engagement owner can delete or restore it");
      require(c["version"]==expected(match),"version_conflict","Engagement changed. Refresh and try again");require(b.value("confirm",false),"confirmation","Confirm this engagement action");
      if(op=="delete")for(const auto &job:store_.list("job",id,-1))require(job["data"].value("state",std::string(""))!="running"&&job["data"].value("state",std::string(""))!="queued","active_jobs","Wait for active jobs to finish or cancel them before deleting this engagement");
      auto data=c["data"];data["deleted"]=op=="delete";auto updated=store_.update(id,c["version"],data);store_.audit(a.id,op+"_engagement",id,{{"recoverable",true}});return {updated};
    }
    if(method=="GET"&&(op=="completions"||op=="saved-projections"))return {store_.list(op=="completions"?"engagement_completion":"projection",id)};
    if(method=="GET"&&op=="closure-review")return {closure_review(store_,c)};
    if(method=="POST"&&op=="close-with-report") {
      keys(b,{"review_digest","notes","confirm"},"");require(a.role!="agent","forbidden","A consultant must confirm closure");require(c["version"]==expected(match),"version_conflict","Engagement changed. Refresh the closure review");require(c["data"].value("status",std::string("active"))!="completed","completed","Reopen before recording another conclusion");require(b.value("confirm",false),"confirmation","Confirm conclusion without a design handoff");
      auto review=closure_review(store_,c);require(!review["running_jobs"].get<bool>(),"active_jobs","Wait for active jobs to finish or cancel them before closing");require(text(b,"review_digest")==review["review_digest"].get<std::string>(),"stale_closure_review","The evidence changed. Preview the final status report again");
      auto notes=text(b,"notes");require(!notes.empty()&&notes.size()<=4000,"closure_reason","Explain why the engagement is being concluded now (1–4000 characters)");
      auto timestamp=std::chrono::duration_cast<std::chrono::seconds>(std::chrono::system_clock::now().time_since_epoch()).count();
      auto completion=save(a,"engagement_completion",id,{{"outcome","concluded_without_handoff"},{"meaning","Concluded with a final status report. No design handoff delivered or architecture approved."},{"name",c["data"]["name"]},{"completed_at",timestamp},{"completed_by",a.id},{"notes",notes},{"assessment",review},{"report_text",review["report_text"].get<std::string>()+"\nConsultant conclusion\n"+notes+"\n"},{"previous_completion_id",c["data"].value("completion_id",std::string(""))}});
      auto data=c["data"];data["status"]="completed";data["completion_outcome"]="concluded_without_handoff";data["completion_id"]=completion["id"];data["completed_at"]=timestamp;auto updated=store_.update(id,c["version"],data);store_.audit(a.id,"close_with_status_report",id,{{"completion_id",completion["id"]}});return {{{"case",updated},{"completion",completion}},201};
    }
    if(method=="POST"&&op=="complete") {
      keys(b,{"result_id","projection_id","notes","confirm_delivery","acknowledge_stale","executive_summary","narrative_version"},"");
      require(a.role!="agent","forbidden","A consultant must confirm delivery");
      require(c["version"]==expected(match),"version_conflict","Engagement changed. Refresh before completing");
      require(c["data"].value("status",std::string("active"))!="completed","completed","Reopen the engagement before recording a new completion");
      require(b.value("confirm_delivery",false),"confirmation","Confirm requirements delivery before completing");
      auto r=scoped(a,text(b,"result_id")),pr=scoped(a,text(b,"projection_id"));
      require(r["type"]=="result"&&pr["type"]=="projection"&&r["case_id"]==id&&pr["case_id"]==id,"completion_scope","Select a calculation and projection from this engagement");
      require(pr["data"]["result_id"]==r["id"],"completion_pair","The projection must reference the selected calculation");
      auto revision=store_.get(r["data"]["revision_id"]),draft=store_.get(revision["data"]["source_draft"]);
      bool stale=draft["version"]!=revision["data"]["source_version"];
      require(!stale||b.value("acknowledge_stale",false),"stale_completion","Newer workload edits exist. Recalculate or explicitly acknowledge delivery of the selected earlier calculation");
      auto notes=b.value("notes",std::string("")),summary=b.value("executive_summary",std::string("")),grammar=b.value("narrative_version",std::string(""));
      require(notes.size()<=4000&&summary.size()<=60000&&grammar.size()<=100,"size","Completion notes or summary exceed the limit");
      auto timestamp=std::chrono::duration_cast<std::chrono::seconds>(std::chrono::system_clock::now().time_since_epoch()).count();
      auto completion=save(a,"engagement_completion",id,{{"meaning","Requirements delivered. Not architecture approval or performance qualification."},{"name",c["data"]["name"]},{"completed_at",timestamp},{"completed_by",a.id},{"notes",notes},{"result_id",r["id"]},{"projection_id",pr["id"]},{"revision_id",revision["id"]},{"result_snapshot",r["data"]},{"projection_snapshot",pr["data"]},{"result_digest",digest(r["data"])},{"projection_digest",digest(pr["data"])},{"executive_summary",summary},{"narrative_version",grammar},{"earlier_calculation_acknowledged",stale},{"previous_completion_id",c["data"].value("completion_id",std::string(""))}});
      auto data=c["data"];data["status"]="completed";data["completion_outcome"]="requirements_delivered";data["completion_id"]=completion["id"];data["completed_at"]=timestamp;
      auto updated=store_.update(id,c["version"],data);store_.audit(a.id,"complete_engagement",id,{{"completion_id",completion["id"]}});return {{{"case",updated},{"completion",completion}},201};
    }
    if(method=="POST"&&op=="reopen") {
      keys(b,{"notes"},"");require(a.role!="agent","forbidden","A consultant must reopen the engagement");require(c["version"]==expected(match),"version_conflict","Engagement changed. Refresh before reopening");
      require(c["data"].value("status",std::string("active"))=="completed","status","This engagement is already active");auto notes=b.value("notes",std::string(""));require(notes.size()<=4000,"size","Notes exceed the limit");
      auto data=c["data"];data["status"]="active";data.erase("copilot_resume_session_id");
      auto drafts=store_.list("draft",id);if(!drafts.empty()){
        auto d=drafts[0];auto catalog=read_json(root_+"/knowledge/guided-intake.json");auto review=assisted_review(d["data"],catalog);
        if(review.value("can_copy",false)){
          auto previous=store_.list("copilot_session",id);auto prior=previous.empty()?Json::object():previous[0]["data"];
          auto session=save(a,"copilot_session",id,{{"input",assisted_input(d["data"])},{"revision",1},{"draft_id",d["id"]},{"draft_version",d["version"]},{"classification",prior.value("classification",std::string("corporate"))},{"profile_id",prior.value("profile_id",std::string(""))},{"turns",0},{"state","open"},{"author",a.id},{"reopened_from_completion",data["completion_id"]}});
          data["copilot_resume_session_id"]=session["id"];
        }
      }
      auto updated=store_.update(id,c["version"],data);store_.audit(a.id,"reopen_engagement",id,{{"completion_id",data["completion_id"]},{"notes",notes}});return {updated};
    }
    if (method == "PATCH" && op.empty()) {
      keys(b, {"name", "archived", "members", "agent_compile_limit", "agent_proposal_limit"}, "");
      auto d = c["data"];
      for (auto it = b.begin(); it != b.end(); ++it)
        d[it.key()] = it.value();
      if (b.contains("name"))
        require(b["name"].is_string() && !b["name"].get<std::string>().empty() &&
                    b["name"].get<std::string>().size() <= 240,
                "name", "Case name length 1–240");
      if (b.contains("archived"))
        require(b["archived"].is_boolean(), "type", "archived must be boolean");
      if (b.contains("agent_compile_limit")) {
        require(c["data"]["owner"] == a.id, "owner", "Only the owner may change agent budgets");
        require(b["agent_compile_limit"].is_number_integer() &&
                    b["agent_compile_limit"].get<int>() >= 0 &&
                    b["agent_compile_limit"].get<int>() <= 100,
                "budget", "Agent compilation limit must be 0–100");
      }
      if (b.contains("agent_proposal_limit")) {
        require(c["data"]["owner"] == a.id, "owner", "Only owner may change proposal budgets");
        require(b["agent_proposal_limit"].is_number_integer() &&
                    b["agent_proposal_limit"].get<int>() >= 0 &&
                    b["agent_proposal_limit"].get<int>() <= 100,
                "budget", "Proposal budget must be 0–100");
      }
      if (b.contains("members")) {
        require(c["data"]["owner"] == a.id, "owner", "Only owner can change membership");
        require(b["members"].is_array(), "members", "Expected array");
        for (auto m : b["members"])
          require(m.is_string(), "member", "Expected member identity");
      }
      auto r = store_.update(id, expected(match), d);
      store_.audit(a.id, "update_case", id, b);
      return {r};
    }
    if (op == "drafts" && method == "POST") {
      validate_workload(b);
      return {save(a, "draft", id, b), 201};
    }
    if (op == "drafts" && method == "GET")
      return {store_.list("draft", id)};
    if (op == "proposals" && method == "GET")
      return {store_.list("observation_proposal", id)};
    if (op == "runs" && method == "GET")
      return {store_.list("result", id)};
    if (op == "audit" && method == "GET")
      return {store_.audits(id)};
  }
  if (top == "drafts") {
    auto d = scoped(a, id);
    require(d["type"] == "draft", "type", "Expected draft");
    if (method == "GET")
      return {d};
    case_access(a, d["case_id"], true);
    if (method == "PATCH") {
      validate_workload(b);
      auto saved=b;
      if(saved.contains("characterization")&&saved["characterization"].contains("guided_input")) {
        auto review=assisted_review(saved,read_json(root_ + "/knowledge/guided-intake.json"));
        if(review.value("compatible",false)){saved["characterization"].erase("advanced_modified");saved["characterization"]["guided_input"]=assisted_input(saved);}
        else saved["characterization"]["advanced_modified"]=true;
      }
      auto r = store_.update(id, expected(match), saved);
      store_.audit(a.id, "update_draft", d["case_id"], {{"version", r["version"]}});
      return {r};
    }
    if (method == "POST" && op == "validate")
      return {validate_workload(d["data"])};
    if (method == "POST" && op == "freeze") {
      if (d["version"] != expected(match))
        throw Error("version_conflict", "Draft version changed", "", 409);
      auto norm = normalize_workload(d["data"]);
      return {save(a, "revision", d["case_id"],
                   {{"workload", norm},
                    {"digest", digest(norm)},
                    {"source_draft", id},
                    {"source_version", d["version"]}}),
              201};
    }
  }
  if (top == "observation-proposals" && method == "POST") {
    keys(b, {"draft_id", "rows"}, "");
    auto draft = scoped(a, text(b, "draft_id"));
    require(draft["type"] == "draft", "type", "Expected draft");
    auto engagement = case_access(a, draft["case_id"], true);
    if (a.role == "agent") {
      int used = 0;
      for (auto p : store_.list("observation_proposal", draft["case_id"], -1))
        if (p["data"]["author"] == a.id)
          ++used;
      require(used < engagement["data"].value("agent_proposal_limit", 0), "agent_budget",
              "No remaining authorized proposals");
    }
    require(b.at("rows").is_array() && !b["rows"].empty() && b["rows"].size() <= 100,
            "proposal_rows", "Supply 1–100 proposed observations");
    for (const auto &row : b["rows"]) {
      const auto &obs = row.at("observation");
      require(obs.value("origin", "") == "agent" && obs.value("state", "") == "assumed" &&
                  !obs.value("accepted", false),
              "proposal_origin",
              "Agent observations must remain unaccepted assumptions pending human review");
    }
    auto preview = preview_import(draft["data"], b["rows"]);
    require(preview["rejected"].empty(), "proposal_invalid", "Proposal contains invalid rows");
    return {save(a, "observation_proposal", draft["case_id"],
                 {{"draft_id", draft["id"]},
                  {"draft_version", draft["version"]},
                  {"rows", b["rows"]},
                  {"author", a.id},
                  {"state", "proposed"}}),
            201};
  }
  if (top == "proposal-reviews" && method == "POST") {
    keys(b, {"proposal_id", "accept_rows", "rationale"}, "");
    auto proposal = scoped(a, text(b, "proposal_id"));
    require(proposal["type"] == "observation_proposal", "type", "Expected proposal");
    case_access(a, proposal["case_id"], true);
    auto draft = store_.get(proposal["data"]["draft_id"]);
    if (draft["version"] != proposal["data"]["draft_version"])
      throw Error("version_conflict", "Draft changed; review a fresh proposal", "", 409);
    require(!text(b, "rationale").empty(), "rationale", "Review rationale required");
    require(b.at("accept_rows").is_array(), "rows", "Explicit accepted row indexes required");
    Json rows = Json::array();
    std::set<int> seen;
    for (const auto &index : b["accept_rows"]) {
      require(index.is_number_integer(), "row", "Expected integer row index");
      int n = index.get<int>();
      require(n >= 0 && static_cast<size_t>(n) < proposal["data"]["rows"].size() &&
                  seen.insert(n).second,
              "row", "Invalid or repeated row index");
      auto row = proposal["data"]["rows"][n];
      row["observation"]["accepted"] = true;
      rows.push_back(row);
    }
    auto preview = preview_import(draft["data"], rows);
    require(preview["rejected"].empty(), "proposal_invalid", "Accepted rows no longer validate");
    auto updated = store_.update(draft["id"], draft["version"], preview["proposed_workload"]);
    auto review = save(a, "proposal_review", draft["case_id"],
                       {{"proposal_id", proposal["id"]},
                        {"accept_rows", b["accept_rows"]},
                        {"rationale", b["rationale"]},
                        {"reviewer", a.id},
                        {"draft_version", updated["version"]}});
    return {{{"draft", updated}, {"review", review}}, 201};
  }
  if (top == "import-previews" && method == "POST") {
    auto draft = scoped(a, text(b, "draft_id"));
    require(draft["type"] == "draft", "type", "Expected draft");
    case_access(a, draft["case_id"], true);
    auto preview = preview_import(draft["data"], b.at("rows"));
    preview["draft_id"] = draft["id"];
    preview["draft_version"] = draft["version"];
    return {save(a, "import_preview", draft["case_id"], preview), 201};
  }
  if (top == "import-commits" && method == "POST") {
    auto preview = scoped(a, text(b, "preview_id"));
    require(preview["type"] == "import_preview", "type", "Expected immutable preview");
    case_access(a, preview["case_id"], true);
    require(preview["data"]["rejected"].empty() || b.value("accept_partial", false),
            "import_rejections", "Review rejected rows before accepting partial import");
    auto updated = store_.update(preview["data"]["draft_id"], preview["data"]["draft_version"],
                                 preview["data"]["proposed_workload"]);
    store_.audit(a.id, "commit_import", preview["case_id"], {{"preview_id", preview["id"]}});
    return {updated};
  }
  if (top == "packs") {
    if (method == "GET" && id.empty())
      return {store_.list("pack")};
    if (method == "POST" && id.empty()) {
      require(a.role == "curator" || a.role == "admin", "forbidden", "Curator permission required");
      validate_pack(b);
      for (const auto &existing : store_.list("pack", "", 10000))
        if (existing["data"]["pack"]["id"] == b["id"] &&
            existing["data"]["pack"]["version"] == b["version"])
          require(existing["data"]["digest"] == digest(b), "immutable_version",
                  "Pack version already names different content");
      return {save(a, "pack", "", {{"pack", b}, {"digest", digest(b)}, {"author", a.id}}), 201};
    }
    auto pack = scoped(a, id);
    require(pack["type"] == "pack", "type", "Expected pack");
    if (method == "GET")
      return {pack};
    if (method == "POST" && op == "activate") {
      require(a.role == "approver" || a.role == "admin", "forbidden",
              "Approver permission required");
      auto channel = text(b, "channel");
      require(channel == "demonstration" || channel == "production", "channel",
              "Expected demonstration or production");
      auto lock = resolve_knowledge(pack["data"]["digest"], [&](const std::string &hash) -> Json {
        for (auto record : store_.list("pack", "", 10000))
          if (record["data"]["digest"] == hash)
            return record["data"]["pack"];
        throw Error("dependency_missing", "Required pack not imported", hash);
      });
      if (channel == "production") {
        require(lock["resolved"]["channel"] == "qualified", "synthetic_activation",
                "Production lock includes synthetic evidence");
        require(pack["data"]["pack"]["channel"] == "qualified", "synthetic_activation",
                "Synthetic evidence cannot be activated for production");
        require(pack["data"]["author"] != a.id, "separation",
                "Evidence author cannot approve production activation");
        auto report = store_.get(text(b, "qualification_report_id"));
        require(report["type"] == "qualification_report" &&
                    report["data"]["report"]["pass"].get<bool>(),
                "qualification_failed", "Passing held-out qualification required");
        require(report["data"]["report"]["pack_digest"] == pack["data"]["digest"],
                "qualification_mismatch", "Qualification refers to another pack");
        require(report["data"]["author"] != a.id, "separation",
                "Qualification author cannot approve production activation");
      }
      return {save(a, "activation", "",
                   {{"pack_id", id},
                    {"pack_digest", pack["data"]["digest"]},
                    {"knowledge_lock", lock},
                    {"channel", channel},
                    {"withdrawn", false},
                    {"approved_by", a.id},
                    {"qualification_report_id", b.value("qualification_report_id", "")}}),
              201};
    }
  }
  if (top == "qualification-protocols") {
    if (method == "GET")
      return {id.empty() ? store_.list("qualification_protocol") : scoped(a, id)};
    if (method == "POST" && id.empty()) {
      require(a.role == "curator" || a.role == "admin", "forbidden", "Curator required");
      validate_protocol(b);
      return {save(a, "qualification_protocol", "",
                   {{"protocol", b}, {"author", a.id}, {"digest", digest(b)}}),
              201};
    }
  }
  if (top == "qualification-reports" && method == "GET")
    return {id.empty() ? store_.list("qualification_report") : scoped(a, id)};
  if (top == "qualification-runs" && method == "POST") {
    require(a.role == "curator" || a.role == "admin", "forbidden", "Curator required");
    auto protocol = store_.get(text(b, "protocol_id"));
    require(protocol["type"] == "qualification_protocol", "type", "Expected frozen protocol");
    auto report = evaluate_qualification(protocol["data"]["protocol"], b.at("dataset"));
    return {save(a, "qualification_report", "",
                 {{"report", report},
                  {"protocol_id", protocol["id"]},
                  {"dataset", b["dataset"]},
                  {"author", a.id}}),
            201};
  }
  if (top == "activations") {
    if (method == "GET" && id.empty())
      return {store_.list("activation")};
    auto r = scoped(a, id);
    require(r["type"] == "activation", "type", "Expected activation");
    if (method == "GET" && op == "impact") {
      Json runs = Json::array();
      for (auto job : store_.list("job", "", -1)) {
        if (job["data"].value("activation_id", "") != id)
          continue;
        try {
          case_access(a, job["case_id"]);
        } catch (const Error &) {
          continue;
        }
        runs.push_back({{"job_id", job["id"]},
                        {"case_id", job["case_id"]},
                        {"result_id", job["data"].value("result_id", "")}});
      }
      return {{{"activation_id", id}, {"authorized_dependents", runs}}};
    }
    if (method == "GET")
      return {r};
    if (method == "POST" && op == "withdraw") {
      require(a.role == "admin" || a.role == "approver", "forbidden", "Approver required");
      auto d = r["data"];
      d["withdrawn"] = true;
      auto res = store_.update(id, r["version"], d);
      store_.audit(a.id, "withdraw_activation", "", {{"id", id}});
      return {res};
    }
  }
  if (top == "compilations" && method == "POST") {
    keys(b, {"revision_id", "activation_id"}, "");
    auto rev = scoped(a, text(b, "revision_id"));
    require(rev["type"] == "revision", "type", "Expected revision");
    case_access(a, rev["case_id"], true);
    if (a.role == "agent") {
      auto engagement = case_access(a, rev["case_id"]);
      int limit = engagement["data"].value("agent_compile_limit", 0), used = 0;
      for (auto job : store_.list("job", rev["case_id"], 10000))
        if (job["data"]["actor"] == a.id)
          ++used;
      require(used < limit, "agent_budget",
              "No remaining authorized agent compilations for this case");
    }

    Json pack = {{"schema_version", "1.0"},
                 {"id", "empty"},
                 {"version", "1"},
                 {"channel", "synthetic"},
                 {"profiles", Json::array()}};
    std::string activation_id;
    if (b.contains("activation_id") && !b["activation_id"].is_null()) {
      activation_id = text(b, "activation_id");
      auto activation = scoped(a, activation_id);
      require(activation["type"] == "activation" && !activation["data"]["withdrawn"].get<bool>(),
              "activation", "Activation unavailable");
      pack = activation["data"]["knowledge_lock"]["resolved"];
    }
    auto job = save(a, "job", rev["case_id"],
                    {{"state", "queued"},
                     {"revision_id", rev["id"]},
                     {"workload", rev["data"]["workload"]},
                     {"knowledge", pack},
                     {"activation_id", activation_id},
                     {"engine_version", engine_version},
                     {"actor", a.id},
                     {"attempt", 0}});
    return {job, 202};
  }
  if (top == "jobs") {
    auto j = scoped(a, id);
    require(j["type"] == "job", "type", "Expected job");
    if (method == "GET") {
      auto clean = j;
      clean["data"].erase("workload");
      clean["data"].erase("knowledge");
      for(auto k:{"context","profile","sources","session_snapshot","catalog","arguments"})clean["data"].erase(k);
      return {clean};
    }
    if (method == "POST" && op == "reconcile") {
      case_access(a, j["case_id"], true);
      require(j["data"].value("kind", "compile") == "neon" &&
                  j["data"]["state"] == "outcome_unknown",
              "reconciliation_state", "Only uncertain downstream design tool submissions may be reconciled");
      auto assessment = assess(j["data"]["projection"], b.at("external_result"));
      assessment["external_result"] = b["external_result"];
      assessment["reconciliation_source"] = text(b, "source");
      auto record = save(a, "assessment", j["case_id"], assessment);
      auto d = j["data"];
      d["state"] = "reconciled";
      d["assessment_id"] = record["id"];
      return {store_.update(id, j["version"], d)};
    }
    if (method == "POST" && op == "cancel") {
      if(j["case_id"]!="")case_access(a, j["case_id"], true);
      else require(a.role=="admin","forbidden","Administrator required");
      auto d = j["data"];
      if (d["state"] == "queued")
        d["state"] = "cancelled";
      else if (d["state"] == "running")
        d["state"] = "cancel_requested";
      return {store_.update(id, j["version"], d)};
    }
  }
  if (top == "results" || top == "revisions" || top == "projections" || top == "reports" ||
      top == "assessments" || top == "decisions") {
    if (method == "GET") {
      auto r = scoped(a, id);
      std::map<std::string, std::string> types = {
          {"results", "result"}, {"revisions", "revision"},     {"projections", "projection"},
          {"reports", "report"}, {"assessments", "assessment"}, {"decisions", "decision"}};
      require(r["type"] == types[top], "type", "Wrong record type");
      return {r};
    }
  }
  if (top == "neon-projections" && method == "POST") {
    auto result = scoped(a, text(b, "result_id"));
    require(result["type"] == "result", "type", "Expected result");
    case_access(a, result["case_id"], true);
    auto projection = project(result["data"]["result"], b.at("mapping"));
    projection["result_id"] = result["id"];
    return {save(a, "projection", result["case_id"], projection), 201};
  }
  if (top == "external-result-imports" && method == "POST") {
    auto pr = scoped(a, text(b, "projection_id"));
    require(pr["type"] == "projection", "type", "Expected projection");
    case_access(a, pr["case_id"], true);
    auto result = assess(pr["data"], b.at("external_result"));
    result["projection_id"] = pr["id"];
    result["external_result"] = b["external_result"];
    return {save(a, "assessment", pr["case_id"], result), 201};
  }
  if (top == "neon-submissions" && method == "POST") {
    auto target = neon_target();
    keys(b, {"projection_id", "confirm_experimental_submission"}, "");
    require(b.value("confirm_experimental_submission", false), "decision_required",
            "Explicit experimental submission decision required");
    auto pr = scoped(a, text(b, "projection_id"));
    require(pr["type"] == "projection", "type", "Expected immutable projection");
    case_access(a, pr["case_id"], true);
    return {save(a, "job", pr["case_id"],
                 {{"state", "queued"},
                  {"kind", "neon"},
                  {"projection_id", pr["id"]},
                  {"projection", pr["data"]},
                  {"target", target},
                  {"actor", a.id},
                  {"attempt", 0}}),
            202};
  }
  if (top == "recommendation-decisions" && method == "POST") {
    auto r = scoped(a, text(b, "result_id"));
    require(r["type"] == "result", "type", "Expected result");
    case_access(a, r["case_id"], true);
    auto state = text(b, "state");
    require(state == "selected" || state == "finalized", "selection",
            "Expected selected or finalized");
    if (state == "finalized")
      require(a.role == "architect" || a.role == "admin", "forbidden", "Architect required");
    auto candidate = text(b, "candidate_id");
    bool found = false;
    for (auto c : r["data"]["result"]["candidates"])
      if (c["id"] == candidate && c["status"] != "fail")
        found = true;
    require(found, "candidate", "Select a nonfailed existing candidate");
    return {save(a, "decision", r["case_id"],
                 {{"result_id", r["id"]},
                  {"candidate_id", candidate},
                  {"state", state},
                  {"rationale", text(b, "rationale")},
                  {"actor", a.id},
                  {"engineering_status_unchanged", true}}),
            201};
  }
  if (top == "reports" && method == "POST") {
    auto r = scoped(a, text(b, "result_id"));
    require(r["type"] == "result", "type", "Expected result");
    case_access(a, r["case_id"], true);
    return {save(a, "report", r["case_id"],
                 {{"result_id", r["id"]},
                  {"template_version", "1.0"},
                  {"result_digest", r["data"]["result"]["semantic_digest"]},
                  {"title", "Anubis workload requirements"},
                  {"summary", "Scope and qualifications apply to every recommendation. No "
                              "production evidence is bundled."},
                  {"result", r["data"]["result"]}}),
            201};
  }
  if (top == "comparisons" && method == "POST") {
    auto l = scoped(a, text(b, "left_id")), r = scoped(a, text(b, "right_id"));
    require(l["type"] == "result" && r["type"] == "result", "type", "Expected results");
    auto x = l["data"]["result"], y = r["data"]["result"];
    return {{{"left_id", l["id"]},
             {"right_id", r["id"]},
             {"workload_changed", x["workload_digest"] != y["workload_digest"]},
             {"knowledge_changed", x["knowledge_digest"] != y["knowledge_digest"]},
             {"attribution",
              "Combined changes require a controlled scenario fork for causal attribution"},
             {"diff", Json::diff(x, y)}}};
  }
  throw Error("not_found", "Operation not implemented", "", 404);
}
static int64_t lease_clock() {
  return std::chrono::duration_cast<std::chrono::seconds>(
             std::chrono::system_clock::now().time_since_epoch())
      .count();
}
void Service::work() {
  const auto worker_id = new_id("worker");
  while (true) {
    Json job;
    {
      std::unique_lock lock(mutex_);
      wake_.wait_for(lock, std::chrono::milliseconds(100), [&] { return stopping_; });
      if (stopping_)
        return;
      try {
        store_.begin();
        for (auto j : store_.list("job", "", -1)) {
          auto d = j["data"];
          bool expired = (d["state"] == "running" || d["state"] == "cancel_requested") &&
                         d.value("lease_until", int64_t(0)) < lease_clock();
          if (expired &&
              (d.value("kind", "compile") != "compile" || d["state"] == "cancel_requested")) {
            d["state"] = d.value("kind", "compile") != "compile" ? "outcome_unknown" : "cancelled";
            store_.update(j["id"], j["version"], d);
            continue;
          }
          if (d["state"] != "queued" && !expired)
            continue;
          d["state"] = "running";
          d["attempt"] = d["attempt"].get<int>() + 1;
          d["worker_id"] = worker_id;
          d["lease_until"] = lease_clock() + 300;
          job = store_.update(j["id"], j["version"], d);
          break;
        }
        store_.commit();
      } catch (...) {
        try {
          store_.rollback();
        } catch (...) {
        }
        continue;
      }
    }
    if (job.is_null())
      continue;
    Json result, failure, provider_attempts=Json::array();
    try {
      if (job["data"].value("kind", "compile") == "neon")
        result = submit_neon(job["data"]["target"], job["data"]["projection"]["payload"]);
      else if(job["data"].value("kind","")=="copilot"||job["data"].value("kind","")=="copilot_test") {
        auto context=job["data"]["context"];
        for(int correction=0;;++correction){
         try {
          result=execute_model(job["data"]["profile"],context);
          if(job["data"]["kind"]=="copilot")result["proposal"]=fact_proposal(result["output"],job["data"]["session_snapshot"],job["data"]["sources"],job["data"]["catalog"],context["architecture_library"],true);
          break;
         }catch(const Error &e){
          provider_attempts.push_back({{"error",error_json(e)},{"usage",result.is_object()?result.value("usage",Json::object()):Json::object()},{"output",result.is_object()?result.value("output",Json::object()):Json::object()}});
          if(job["data"]["kind"]=="copilot"&&correction==1&&result.is_object()&&result.contains("output")){
           try{result["proposal"]=partial_fact_proposal(result["output"],job["data"]["session_snapshot"],job["data"]["sources"],job["data"]["catalog"],context["architecture_library"]);break;}catch(const Error &){throw e;}
          }
          if(job["data"]["kind"]!="copilot"||correction==1||e.code=="provider_billing"||e.code=="provider_authentication"||e.code=="provider_rate_limit"||e.code=="provider_unavailable")throw;
          {std::lock_guard guard(mutex_);auto current=store_.get(job["id"]);require(current["data"]["state"]=="running","cancelled","Model turn cancelled before correction");}
          context["correction"]={{"validation_error",error_json(e)},{"previous_output",result.is_object()?result.value("output",Json::object()):Json::object()},{"instruction","Correct this draft once, preserving valid facts and adding missing explicit architecture characteristics. Do not invent values. Use unknown for unstated facts. Do not discard all useful facts."}};
         }
        }
        result["correction_attempts"]=provider_attempts;
        if(job["data"]["kind"]!="copilot") {auto empty=copilot_empty("Capability check");copilot_proposal(result["output"],{{"input",empty},{"revision",1}},Json::array(),read_json(root_+"/knowledge/guided-intake.json"));require(result["output"]["changes"].empty(),"capability_test","Capability test must return no changes");}
      } else if(job["data"].value("kind","")=="mcp_test") result=execute_mcp(job["data"]["profile"],"",Json::object());
      else if(job["data"].value("kind","")=="mcp_import") result=execute_mcp(job["data"]["profile"],job["data"]["tool"],job["data"]["arguments"]);
      else
        result = compile(job["data"]["workload"], job["data"]["knowledge"]);
    } catch (const Error &e) {
      failure = error_json(e);
    } catch (const std::exception &) {
      failure = {{"error",
                  {{"code", "compiler_failure"},
                   {"message", "Execution failed without publishing a result"}}}};
    }
    std::lock_guard lock(mutex_);
    try {
      store_.begin();
      auto latest = store_.get(job["id"]);
      auto d = latest["data"];
      if(!provider_attempts.empty())d["correction_attempts"]=provider_attempts;
      if (d.value("worker_id", "") != worker_id || d["attempt"] != job["data"]["attempt"] ||
          d.value("lease_until", int64_t(0)) < lease_clock()) {
        store_.commit();
        continue;
      }
      if (d["state"] == "cancel_requested" && d.value("kind", "compile") != "neon") {
        d["state"] = "cancelled";
        store_.update(job["id"], latest["version"], d);
        store_.commit();
        continue;
      }
      if (d["state"] != "running" && d["state"] != "cancel_requested") {
        store_.commit();
        continue;
      }
      if((d.value("kind","")=="copilot"||d.value("kind","")=="mcp_import")&&job["case_id"]!="")case_access({d["actor"],"worker"},job["case_id"]);
      if (!failure.is_null()) {
        d["state"] =
            failure["error"].value("code", "") == "outcome_unknown" ? "outcome_unknown" : "failed";
        d["error"] = failure["error"];
        if(d.value("kind","")=="copilot_test"||d.value("kind","")=="mcp_test") {auto profile=store_.get(d["profile_id"]);if(profile["version"]==d["profile_version"]){auto pd=profile["data"];pd["health"]="failed";pd["tested_job"]=job["id"];store_.update(profile["id"],profile["version"],pd);}}
      } else if(d.value("kind","")=="copilot_test"||d.value("kind","")=="mcp_test") {
        auto profile=store_.get(d["profile_id"]);require(profile["version"]==d["profile_version"],"profile_changed","Profile changed during test");auto pd=profile["data"];pd["health"]="capability_passed";pd["tested_job"]=job["id"];store_.update(profile["id"],profile["version"],pd);d["state"]="succeeded";d["qualification"]="Capability only. Interpretation quality not qualified";if(d["kind"]=="mcp_test") {d["tools"]=Json::array();for(auto t:result["tools"]) {t["schema_digest"]=digest(t["inputSchema"]);d["tools"].push_back(t);}}
      } else if(d.value("kind","")=="copilot") {
        auto session=store_.get(d["session_id"]);auto profile=store_.get(d["profile_id"]);
        if(session["data"]["revision"]!=d["base_revision"]||profile["version"]!=d["profile_version"]||!profile["data"].value("enabled",false)){d["state"]="failed";d["error"]={{"code","stale_context"},{"message","Inputs or model policy changed. Request a fresh turn"}};}
        else {auto pd=result["proposal"];pd["session_id"]=d["session_id"];pd["author"]=d["actor"];pd["job_id"]=job["id"];auto record=save({d["actor"],"worker"},"copilot_proposal",job["case_id"],pd);d["proposal_id"]=record["id"];d["state"]="succeeded";d["usage"]=result["usage"];d["correction_attempts"]=result.value("correction_attempts",Json::array());d["provider_request_id"]=result["provider_request_id"];}
      } else if(d.value("kind","")=="mcp_import") {
        auto content=result.dump();require(content.size()<=32000,"source_limit","MCP content exceeds source limit");auto record=save({d["actor"],"worker"},"copilot_source",job["case_id"],{{"session_id",d["session_id"]},{"text",content},{"name",d["tool"]},{"kind","mcp"},{"digest",digest(content)},{"author",d["actor"]}});d["source_id"]=record["id"];d["state"]="succeeded";
      } else if (d.value("kind", "compile") == "neon") {
        auto assessed = assess(d["projection"], result["response"]);
        assessed["transport"] = result;
        assessed["projection_id"] = d["projection_id"];
        auto record = save({d["actor"], "worker"}, "assessment", job["case_id"], assessed);
        d["cancellation_after_dispatch"] = d["state"] == "cancel_requested";
        d["state"] = "succeeded";
        d["assessment_id"] = record["id"];
      } else {
        auto r = save({d["actor"], "worker"}, "result", job["case_id"],
                      {{"result", result},
                       {"revision_id", d["revision_id"]},
                       {"activation_id", d["activation_id"]},
                       {"job_id", job["id"]}});
        d["state"] = "succeeded";
        d["result_id"] = r["id"];
      }
      store_.update(job["id"], latest["version"], d);
      store_.commit();
    } catch (...) {
      try {
        store_.rollback();
        store_.begin();auto failed=store_.get(job["id"]);auto fd=failed["data"];fd["state"]="failed";fd["error"]={{"code","publication_failed"},{"message","Context or policy changed. No result was published"}};store_.update(failed["id"],failed["version"],fd);store_.commit();
      } catch (...) {
      }
    }
  }
}
} // namespace anubis
