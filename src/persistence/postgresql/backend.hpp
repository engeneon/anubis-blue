#pragma once
#include "domain/json.hpp"
struct pg_conn;
namespace anubis {
class PostgresStore {
  pg_conn *db_ = nullptr;
  Json query(const std::string &sql, const std::vector<std::string> &params = {});

public:
  explicit PostgresStore(const std::string &url);
  ~PostgresStore();
  Json get(const std::string &id);
  Json list(const std::string &type, const std::string &cid, int limit);
  Json put(const std::string &type, const std::string &id, const std::string &cid,
           const Json &body);
  Json update(const std::string &id, int64_t expected, const Json &body);
  void begin();
  void commit();
  void rollback();
  void audit(const std::string &actor, const std::string &op, const std::string &cid,
             const Json &details);
  Json audits(const std::string &cid);
};
} // namespace anubis
