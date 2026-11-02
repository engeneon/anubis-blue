#include "persistence/store.hpp"
#include <filesystem>
namespace anubis {
struct Statement {
  sqlite3_stmt *s = nullptr;
  Statement(sqlite3 *db, const char *sql) {
    if (sqlite3_prepare_v2(db, sql, -1, &s, nullptr) != SQLITE_OK)
      throw std::runtime_error(sqlite3_errmsg(db));
  }
  ~Statement() {
    sqlite3_finalize(s);
  }
  void bind(int i, const std::string &v) {
    if (sqlite3_bind_text(s, i, v.c_str(), static_cast<int>(v.size()), SQLITE_TRANSIENT) !=
        SQLITE_OK)
      throw std::runtime_error("bind failed");
  }
  void num(int i, int64_t v) {
    sqlite3_bind_int64(s, i, v);
  }
  int step() {
    auto n = sqlite3_step(s);
    if (n != SQLITE_ROW && n != SQLITE_DONE)
      throw std::runtime_error("Database operation failed");
    return n;
  }
};
static void exec(sqlite3 *db, const char *sql) {
  char *message = nullptr;
  if (sqlite3_exec(db, sql, nullptr, nullptr, &message) != SQLITE_OK) {
    std::string m = message ? message : "Database failure";
    sqlite3_free(message);
    throw std::runtime_error(m);
  }
}
Store::Store(const std::string &path) {
  if (path.starts_with("postgresql://") || path.starts_with("postgres://")) {
    postgres_ = std::make_unique<PostgresStore>(path);
    return;
  }
  if (!std::filesystem::path(path).parent_path().empty())
    std::filesystem::create_directories(std::filesystem::path(path).parent_path());
  if (sqlite3_open(path.c_str(), &db_) != SQLITE_OK)
    throw std::runtime_error("Cannot open database");
  sqlite3_busy_timeout(db_, 5000);
  {
    Statement version(db_, "PRAGMA user_version");
    require(version.step() == SQLITE_ROW && sqlite3_column_int(version.s, 0) <= 1,
            "database_version", "Database schema is newer than this binary; refusing downgrade");
  }
  exec(db_, "PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON; PRAGMA synchronous=FULL; CREATE "
            "TABLE IF NOT EXISTS documents(id TEXT PRIMARY KEY,type TEXT NOT NULL,case_id TEXT NOT "
            "NULL,version INTEGER NOT NULL,body TEXT NOT NULL); CREATE INDEX IF NOT EXISTS "
            "scope_index ON documents(type,case_id); CREATE TABLE IF NOT EXISTS audit(seq INTEGER "
            "PRIMARY KEY AUTOINCREMENT,actor TEXT,operation TEXT,case_id TEXT,details TEXT,created "
            "TEXT DEFAULT CURRENT_TIMESTAMP); PRAGMA user_version=1;");
}
Store::~Store() {
  if (db_)
    sqlite3_close(db_);
}
static Json row(sqlite3_stmt *s) {
  auto t = [&](int i) {
    return std::string(reinterpret_cast<const char *>(sqlite3_column_text(s, i)));
  };
  return {{"id", t(0)},
          {"type", t(1)},
          {"case_id", t(2)},
          {"version", sqlite3_column_int64(s, 3)},
          {"data", parse(t(4))}};
}
Json Store::get(const std::string &id) {
  if (postgres_)
    return postgres_->get(id);
  Statement s(db_, "SELECT id,type,case_id,version,body FROM documents WHERE id=?");
  s.bind(1, id);
  if (s.step() != SQLITE_ROW)
    throw Error("not_found", "Record not found", "", 404);
  return row(s.s);
}
Json Store::list(const std::string &type, const std::string &case_id, int limit) {
  if (postgres_)
    return postgres_->list(type, case_id, limit);
  Statement s(db_, "SELECT id,type,case_id,version,body FROM documents WHERE type=? AND (?='' OR "
                   "case_id=?) ORDER BY rowid DESC LIMIT ?");
  s.bind(1, type);
  s.bind(2, case_id);
  s.bind(3, case_id);
  s.num(4, limit);
  Json a = Json::array();
  while (s.step() == SQLITE_ROW)
    a.push_back(row(s.s));
  return a;
}
Json Store::put(const std::string &type, const std::string &id, const std::string &case_id,
                const Json &body) {
  if (postgres_)
    return postgres_->put(type, id, case_id, body);
  Statement s(db_, "INSERT INTO documents(id,type,case_id,version,body) VALUES(?,?,?,1,?)");
  s.bind(1, id);
  s.bind(2, type);
  s.bind(3, case_id);
  s.bind(4, body.dump());
  s.step();
  return get(id);
}
Json Store::update(const std::string &id, int64_t expected, const Json &body) {
  auto record = get(id);
  require(record["type"] == "copilot_profile" || record["type"] == "copilot_session" || record["type"] == "copilot_proposal" || record["type"] == "draft" || record["type"] == "case" || record["type"] == "job" ||
              record["type"] == "activation" || record["type"] == "submission",
          "immutable", "Historical record is immutable");
  if (postgres_)
    return postgres_->update(id, expected, body);
  Statement s(db_, "UPDATE documents SET version=version+1,body=? WHERE id=? AND version=?");
  s.bind(1, body.dump());
  s.bind(2, id);
  s.num(3, expected);
  s.step();
  if (sqlite3_changes(db_) != 1)
    throw Error("version_conflict", "Record changed; reload and review changes", "", 409);
  return get(id);
}
void Store::begin() {
  if (postgres_) {
    postgres_->begin();
    return;
  }
  exec(db_, "BEGIN IMMEDIATE");
}
void Store::commit() {
  if (postgres_) {
    postgres_->commit();
    return;
  }
  exec(db_, "COMMIT");
}
void Store::rollback() {
  if (postgres_) {
    postgres_->rollback();
    return;
  }
  exec(db_, "ROLLBACK");
}
void Store::audit(const std::string &actor, const std::string &op, const std::string &cid,
                  const Json &details) {
  if (postgres_) {
    postgres_->audit(actor, op, cid, details);
    return;
  }
  Statement s(db_, "INSERT INTO audit(actor,operation,case_id,details) VALUES(?,?,?,?)");
  s.bind(1, actor);
  s.bind(2, op);
  s.bind(3, cid);
  s.bind(4, details.dump());
  s.step();
}
Json Store::audits(const std::string &cid) {
  if (postgres_)
    return postgres_->audits(cid);
  Statement s(db_, "SELECT actor,operation,details,created,seq FROM audit WHERE case_id=? ORDER BY "
                   "seq DESC LIMIT 200");
  s.bind(1, cid);
  Json a = Json::array();
  while (s.step() == SQLITE_ROW) {
    auto t = [&](int i) {
      return std::string(reinterpret_cast<const char *>(sqlite3_column_text(s.s, i)));
    };
    a.push_back({{"actor", t(0)},
                 {"operation", t(1)},
                 {"details", parse(t(2))},
                 {"created", t(3)},
                 {"seq", sqlite3_column_int64(s.s, 4)}});
  }
  return a;
}
void Store::backup(const std::string &path) {
  if (postgres_)
    throw Error("backup_profile", "Use PostgreSQL snapshot tooling for this profile", "", 409);
  sqlite3 *dest = nullptr;
  if (sqlite3_open(path.c_str(), &dest) != SQLITE_OK)
    throw std::runtime_error("Backup destination unavailable");
  auto b = sqlite3_backup_init(dest, "main", db_, "main");
  if (!b) {
    sqlite3_close(dest);
    throw std::runtime_error("Backup initialization failed");
  }
  auto rc = sqlite3_backup_step(b, -1);
  sqlite3_backup_finish(b);
  sqlite3_close(dest);
  if (rc != SQLITE_DONE)
    throw std::runtime_error("Backup failed");
}
} // namespace anubis
