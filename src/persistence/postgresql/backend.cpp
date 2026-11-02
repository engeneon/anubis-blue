#include "persistence/postgresql/backend.hpp"
#ifdef ANUBIS_WITH_POSTGRES
#include <libpq-fe.h>
namespace anubis {
Json PostgresStore::query(const std::string &sql, const std::vector<std::string> &params) {
  std::vector<const char *> values;
  for (const auto &p : params)
    values.push_back(p.c_str());
  auto *r = PQexecParams(db_, sql.c_str(), static_cast<int>(params.size()), nullptr, values.data(),
                         nullptr, nullptr, 0);
  if (!r)
    throw Error("database", "PostgreSQL operation failed", "", 503);
  auto status = PQresultStatus(r);
  if (status != PGRES_TUPLES_OK && status != PGRES_COMMAND_OK) {
    PQclear(r);
    throw Error("database", "PostgreSQL operation failed", "", 503);
  }
  Json rows = Json::array();
  for (int i = 0; i < PQntuples(r); ++i) {
    Json row = Json::object();
    for (int j = 0; j < PQnfields(r); ++j)
      row[PQfname(r, j)] = PQgetisnull(r, i, j) ? Json(nullptr) : Json(PQgetvalue(r, i, j));
    rows.push_back(row);
  }
  PQclear(r);
  return rows;
}
PostgresStore::PostgresStore(const std::string &url) {
  db_ = PQconnectdb(url.c_str());
  if (!db_ || PQstatus(db_) != CONNECTION_OK) {
    if (db_)
      PQfinish(db_);
    db_ = nullptr;
    throw Error("database", "PostgreSQL connection unavailable", "", 503);
  }
  query("CREATE TABLE IF NOT EXISTS documents(id TEXT PRIMARY KEY,type TEXT NOT NULL,case_id TEXT "
        "NOT NULL,version BIGINT NOT NULL,body JSONB NOT NULL,ordinal BIGSERIAL UNIQUE)");
  query("CREATE INDEX IF NOT EXISTS document_scope ON documents(type,case_id)");
  query("CREATE TABLE IF NOT EXISTS audit(seq BIGSERIAL PRIMARY KEY,actor TEXT,operation "
        "TEXT,case_id TEXT,details JSONB,created TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP)");
}
PostgresStore::~PostgresStore() {
  if (db_)
    PQfinish(db_);
}
static Json record(const Json &r) {
  return {{"id", r["id"]},
          {"type", r["type"]},
          {"case_id", r["case_id"]},
          {"version", std::stoll(r["version"].get<std::string>())},
          {"data", parse(r["body"])}};
}
Json PostgresStore::get(const std::string &id) {
  auto rows = query("SELECT id,type,case_id,version,body FROM documents WHERE id=$1", {id});
  if (rows.empty())
    throw Error("not_found", "Record not found", "", 404);
  return record(rows[0]);
}
Json PostgresStore::list(const std::string &type, const std::string &cid, int limit) {
  auto rows = query("SELECT id,type,case_id,version,body FROM documents WHERE type=$1 AND ($2='' "
                    "OR case_id=$2) ORDER BY ordinal DESC LIMIT NULLIF($3::bigint,-1)",
                    {type, cid, std::to_string(limit)});
  Json out = Json::array();
  for (const auto &r : rows)
    out.push_back(record(r));
  return out;
}
Json PostgresStore::put(const std::string &type, const std::string &id, const std::string &cid,
                        const Json &body) {
  query("INSERT INTO documents(id,type,case_id,version,body) VALUES($1,$2,$3,1,$4::jsonb)",
        {id, type, cid, body.dump()});
  return get(id);
}
Json PostgresStore::update(const std::string &id, int64_t expected, const Json &body) {
  auto rows = query("UPDATE documents SET version=version+1,body=$1::jsonb WHERE id=$2 AND "
                    "version=$3::bigint RETURNING id",
                    {body.dump(), id, std::to_string(expected)});
  if (rows.empty())
    throw Error("version_conflict", "Record changed; review latest version", "", 409);
  return get(id);
}
void PostgresStore::begin() {
  query("BEGIN");
  query("SELECT pg_advisory_xact_lock(681247101)");
}
void PostgresStore::commit() {
  query("COMMIT");
}
void PostgresStore::rollback() {
  query("ROLLBACK");
}
void PostgresStore::audit(const std::string &actor, const std::string &op, const std::string &cid,
                          const Json &d) {
  query("INSERT INTO audit(actor,operation,case_id,details) VALUES($1,$2,$3,$4::jsonb)",
        {actor, op, cid, d.dump()});
}
Json PostgresStore::audits(const std::string &cid) {
  auto rows = query("SELECT actor,operation,details,created,seq FROM audit WHERE case_id=$1 ORDER "
                    "BY seq DESC LIMIT 200",
                    {cid});
  Json out = Json::array();
  for (auto r : rows) {
    r["details"] = parse(r["details"]);
    r["seq"] = std::stoll(r["seq"].get<std::string>());
    out.push_back(r);
  }
  return out;
}
} // namespace anubis
#else
namespace anubis {
PostgresStore::PostgresStore(const std::string &) {
  throw Error("profile_unavailable", "Build with ANUBIS_WITH_POSTGRES for this database profile");
}
PostgresStore::~PostgresStore() = default;
Json PostgresStore::query(const std::string &, const std::vector<std::string> &) {
  throw Error("profile_unavailable", "PostgreSQL not enabled");
}
Json PostgresStore::get(const std::string &) {
  return query("");
}
Json PostgresStore::list(const std::string &, const std::string &, int) {
  return query("");
}
Json PostgresStore::put(const std::string &, const std::string &, const std::string &,
                        const Json &) {
  return query("");
}
Json PostgresStore::update(const std::string &, int64_t, const Json &) {
  return query("");
}
void PostgresStore::begin() {
  query("");
}
void PostgresStore::commit() {
  query("");
}
void PostgresStore::rollback() {
  query("");
}
void PostgresStore::audit(const std::string &, const std::string &, const std::string &,
                          const Json &) {
  query("");
}
Json PostgresStore::audits(const std::string &) {
  return query("");
}
} // namespace anubis
#endif
