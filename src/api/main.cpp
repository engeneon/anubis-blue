#include "application/service.hpp"
#include <fcntl.h>
#include <filesystem>
#include <fstream>
#include <httplib/httplib.h>
#include <iostream>
#include <openssl/crypto.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <unistd.h>
using namespace anubis;
static std::string file(const std::string &p) {
  std::ifstream f(p, std::ios::binary);
  if (!f)
    throw Error("not_found", "File missing", "", 404);
  return {std::istreambuf_iterator<char>(f), {}};
}
int main(int argc, char **argv) {
  try {
    umask(0077);
    std::string root = std::filesystem::current_path(), db = ".anubis/anubis.sqlite";
    int port = 8787;
    for (int i = 1; i < argc; i++) {
      std::string a = argv[i];
      if (a == "--root" && i + 1 < argc)
        root = argv[++i];
      else if (a == "--db" && i + 1 < argc)
        db = argv[++i];
      else if (a == "--port" && i + 1 < argc)
        port = std::stoi(argv[++i]);
      else if (a == "compile" && i + 1 < argc) {
        auto w = parse(file(argv[++i]));
        Json pack = {{"schema_version", "1.0"},
                     {"id", "empty"},
                     {"version", "1"},
                     {"channel", "synthetic"},
                     {"profiles", Json::array()}};
        if (i + 1 < argc)
          pack = parse(file(argv[++i]));
        std::cout << compile(w, pack).dump(2) << '\n';
        return 0;
      } else if (a == "--version") {
        std::cout << engine_version << '\n';
        return 0;
      } else
        throw Error("argument", "Usage: anubis [--root path --db file --port 8787] or compile "
                                "workload.json [pack.json]");
    }
    require(port > 1024 && port < 65536, "port", "Port must be between 1025 and 65535");
    const char *config = std::getenv("ANUBIS_IDENTITIES");
    const char *token = std::getenv("ANUBIS_TOKEN");
    Json identities;
    if (config)
      identities = parse(file(config));
    else {
      require(token && std::string(token).size() >= 24, "authentication",
              "Set ANUBIS_TOKEN to at least 24 random characters, or ANUBIS_IDENTITIES to a "
              "protected identities JSON file");
      identities = Json::array({{{"token", token}, {"id", "local-owner"}, {"role", "admin"}}});
    }
    require(identities.is_array() && !identities.empty(), "identities", "Identity array required");
    for (auto i : identities) {
      require(text(i, "token").size() >= 24, "token", "Token too short");
      text(i, "id");
      auto role = text(i, "role");
      require(role == "admin" || role == "architect" || role == "consultant" || role == "viewer" ||
                  role == "curator" || role == "approver" || role == "agent",
              "role", "Invalid role");
    }
    if (!std::filesystem::path(db).parent_path().empty())
      std::filesystem::create_directories(std::filesystem::path(db).parent_path());
    int lockfd = open((db + ".lock").c_str(), O_CREAT | O_RDWR, 0600);
    require(lockfd >= 0 && flock(lockfd, LOCK_EX | LOCK_NB) == 0, "service_lock",
            "One local service may own a database at a time");
    const auto *database_url = std::getenv("ANUBIS_DATABASE_URL");
    Service service(database_url ? database_url : db, root);
    httplib::Server server;
    server.set_payload_max_length(32 * 1024 * 1024);
    server.set_read_timeout(10, 0);
    server.set_write_timeout(10, 0);
    auto authenticate = [&](const httplib::Request &req) -> Actor {
      auto auth = req.get_header_value("Authorization");
      std::string supplied;
      if (auth.starts_with("Bearer "))
        supplied = auth.substr(7);
      else {
        auto cookie = req.get_header_value("Cookie");
        auto pos = cookie.find("anubis_session=");
        if (pos != std::string::npos) {
          supplied = cookie.substr(pos + 15);
          supplied = supplied.substr(0, supplied.find(';'));
        }
      }
      for (const auto &i : identities) {
        auto t = i["token"].get<std::string>();
        if (t.size() == supplied.size() && CRYPTO_memcmp(t.data(), supplied.data(), t.size()) == 0)
          return {i["id"], i["role"]};
      }
      throw Error("unauthorized", "Authentication required", "", 401);
    };
    auto headers = [&](httplib::Response &res) {
      res.set_header("Cache-Control", "no-store");
      res.set_header("X-Content-Type-Options", "nosniff");
      res.set_header(
          "Content-Security-Policy",
          "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
          "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'");
    };
    server.set_pre_routing_handler([&](const httplib::Request &req, httplib::Response &res) {
      headers(res);
      size_t limit =
          req.path == "/api/v1/external-result-imports" ? 32 * 1024 * 1024 : 2 * 1024 * 1024;
      if (req.body.size() > limit) {
        res.status = 413;
        res.set_content(
            error_json(Error("payload_limit", "Request exceeds operation limit", "", 413)).dump(),
            "application/json");
        return httplib::Server::HandlerResponse::Handled;
      }
      auto host = req.get_header_value("Host");
      if (host != "127.0.0.1:" + std::to_string(port) &&
          host != "localhost:" + std::to_string(port)) {
        res.status = 403;
        res.set_content("Invalid host", "text/plain");
        return httplib::Server::HandlerResponse::Handled;
      }
      if (req.method != "GET") {
        auto origin = req.get_header_value("Origin");
        if (!origin.empty() && origin != "http://127.0.0.1:" + std::to_string(port) &&
            origin != "http://localhost:" + std::to_string(port)) {
          res.status = 403;
          res.set_content("Invalid origin", "text/plain");
          return httplib::Server::HandlerResponse::Handled;
        }
      }
      return httplib::Server::HandlerResponse::Unhandled;
    });
    server.Get("/health", [](const auto &, auto &res) {
      res.set_content(
          Json({{"status", "ready"}, {"version", engine_version}, {"profile", "local"}}).dump(),
          "application/json");
    });
    server.Post("/api/v1/session", [&](const auto &req, auto &res) {
      try {
        authenticate(req);
        auto bearer = req.get_header_value("Authorization");
        require(bearer.starts_with("Bearer "), "token",
                "Bearer authentication required to create session");
        res.set_header("Set-Cookie", "anubis_session=" + bearer.substr(7) +
                                         "; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800");
        res.set_content("{\"authenticated\":true}", "application/json");
      } catch (const Error &e) {
        res.status = e.status;
        res.set_content(error_json(e).dump(), "application/json");
      }
    });
    server.Post("/api/v1/logout", [](const auto &, auto &res) {
      res.set_header("Set-Cookie", "anubis_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0");
      res.set_content("{}", "application/json");
    });
    auto handler = [&](const httplib::Request &req, httplib::Response &res) {
      try {
        auto actor = authenticate(req);
        Json b = Json::object();
        if (!req.body.empty()) {
          require(req.get_header_value("Content-Type").starts_with("application/json"),
                  "content_type", "Expected application/json");
          b = parse(req.body);
        }
        auto reply =
            service.request(actor, req.method, req.path, b, req.get_header_value("If-Match"),
                            req.get_header_value("Idempotency-Key"));
        res.status = reply.status;
        res.set_content(reply.body.dump(), "application/json");
        if (reply.body.contains("version") && reply.body["version"].is_number_integer())
          res.set_header("ETag", std::to_string(reply.body["version"].get<int64_t>()));
      } catch (const Error &e) {
        res.status = e.status;
        res.set_content(error_json(e).dump(), "application/json");
      } catch (const nlohmann::json::exception &) {
        res.status = 422;
        res.set_content(error_json(Error("contract", "Invalid request structure")).dump(),
                        "application/json");
      } catch (const std::exception &e) {
        std::cerr << "Request failed: " << e.what() << '\n';
        res.status = 500;
        res.set_content("{\"error\":{\"code\":\"internal\",\"message\":\"Operation failed\"}}",
                        "application/json");
      }
    };
    server.Get(R"(/api/v1/.*)", handler);
    server.Post(R"(/api/v1/.*)", handler);
    server.Patch(R"(/api/v1/.*)", handler);
    server.Get("/", [&](const auto &, auto &res) {
      try {
        res.set_content(file(root + "/ui/dist/index.html"), "text/html");
      } catch (const Error &) {
        res.status = 503;
        res.set_content("Build the UI with npm run build.", "text/plain");
      }
    });
    for (auto name : {"app.js", "copilot.js", "fact-review.js", "projection-summary.js", "help.js", "discovery.js", "guided.js", "readiness.js", "explanation.js", "system-diagram.js", "user-guide.html", "copilot-guide.txt", "anubis-logo.png", "style.css"})
      server.Get("/" + std::string(name), [&, name](const auto &, auto &res) {
        try {
          res.set_content(file(root + "/ui/dist/" + name),
                          std::string(name).ends_with("txt") ? "text/plain; charset=utf-8" : std::string(name).ends_with("png") ? "image/png" : std::string(name).ends_with("css") ? "text/css" : std::string(name).ends_with("html") ? "text/html" : "text/javascript");
        } catch (const Error &) {
          res.status = 404;
        }
      });
    std::cout << "Anubis local service: http://127.0.0.1:" << port << " (authentication required)"
              << std::endl;
    if (!server.listen("127.0.0.1", port))
      throw std::runtime_error("Cannot bind local port");
    close(lockfd);
    return 0;
  } catch (const Error &e) {
    std::cerr << error_json(e).dump() << '\n';
    return 1;
  } catch (const std::exception &e) {
    std::cerr << e.what() << '\n';
    return 1;
  }
}
