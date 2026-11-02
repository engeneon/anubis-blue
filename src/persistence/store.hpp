#pragma once
#include "domain/json.hpp"
#include "persistence/postgresql/backend.hpp"
#include <memory>
#include <sqlite3.h>
namespace anubis {
class Store {
  sqlite3 *db_ = nullptr;
  std::unique_ptr<PostgresStore> postgres_;

public:
  explicit Store(const std::string &path);
  ~Store();
  Store(const Store &) = delete;
  bool shared() const {
    return bool(postgres_);
  }
  Json get(const std::string &id);
  Json list(const std::string &type, const std::string &case_id = "", int limit = 200);
  Json put(const std::string &type, const std::string &id, const std::string &case_id,
           const Json &body);
  Json update(const std::string &id, int64_t expected, const Json &body);
  void begin();
  void commit();
  void rollback();
  void audit(const std::string &actor, const std::string &operation, const std::string &case_id,
             const Json &details);
  Json audits(const std::string &case_id);
  void backup(const std::string &path);
};
} // namespace anubis
