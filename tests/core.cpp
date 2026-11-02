#include "compiler/compiler.hpp"
#include <fstream>
#include <iostream>
using namespace anubis;
int main(int argc, char **argv) {
  try {
    require(argc == 2, "test", "Root required");
    require(Rational::decimal("1.25") == Rational(5, 4), "test", "Exact rational");
    std::ifstream f(std::string(argv[1]) + "/tests/fixtures/meridian.json");
    Json w;
    f >> w;
    auto r = compile(w, {{"schema_version", "1.0"},
                         {"id", "empty"},
                         {"version", "1"},
                         {"channel", "synthetic"},
                         {"profiles", Json::array()}});
    require(r["candidates"].empty(), "test", "No unsupported recommendation");
    std::cout << "Core smoke passed\n";
    return 0;
  } catch (const std::exception &e) {
    std::cerr << e.what() << '\n';
    return 1;
  }
}
