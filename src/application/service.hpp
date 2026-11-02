#pragma once
#include "compiler/compiler.hpp"
#include "persistence/store.hpp"
#include <condition_variable>
#include <mutex>
#include <thread>
namespace anubis {
struct Actor {
  std::string id, role;
};
struct Reply {
  Json body;
  int status = 200;
};
class Service {
  Store store_;
  std::mutex mutex_;
  std::condition_variable wake_;
  bool stopping_ = false;
  std::thread worker_;
  std::string root_, database_;
  Json scoped(const Actor &, const std::string &id);
  Json case_access(const Actor &, const std::string &id, bool write = false);
  Json save(const Actor &, const std::string &type, const std::string &cid, const Json &body);
  Reply dispatch(const Actor &, const std::string &method, const std::vector<std::string> &path,
                 const Json &body, const std::string &match);
  Reply copilot_dispatch(const Actor &, const std::string &, const std::vector<std::string> &, const Json &, const std::string &);
  void work();

public:
  Service(const std::string &database, const std::string &root);
  ~Service();
  Reply request(const Actor &, const std::string &method, const std::string &path, const Json &body,
                const std::string &match, const std::string &idem);
};
std::string new_id(const std::string &prefix);
} // namespace anubis
