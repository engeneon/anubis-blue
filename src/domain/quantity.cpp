#include "domain/quantity.hpp"
#include <limits>
#include <map>
#include <numeric>
namespace anubis {
static std::int64_t safe(__int128 x) {
  require(x <= INT64_MAX && x >= -INT64_MAX, "overflow",
          "Exact arithmetic exceeds signed 64-bit range");
  return static_cast<std::int64_t>(x);
}
Rational::Rational(std::int64_t n, std::int64_t d) {
  require(d > 0 && n != INT64_MIN, "rational", "Invalid rational denominator or numerator");
  auto g = std::gcd(n, d);
  n_ = n / g;
  d_ = d / g;
}
Rational Rational::decimal(const std::string &s) {
  require(!s.empty() && s.size() <= 32, "number", "Expected bounded decimal string");
  bool dot = false, neg = false;
  __int128 n = 0, d = 1;
  size_t i = 0;
  if (s[0] == '-') {
    neg = true;
    i++;
  }
  require(i < s.size(), "number", "Missing digits");
  int digits = 0;
  for (; i < s.size(); i++) {
    char c = s[i];
    if (c == '.' && !dot) {
      dot = true;
      continue;
    }
    require(c >= '0' && c <= '9', "number", "Only decimal notation is supported");
    digits++;
    n = n * 10 + c - '0';
    if (dot)
      d *= 10;
    safe(n);
    safe(d);
  }
  require(digits > 0 && s.back() != '.', "number", "Invalid decimal");
  return Rational(safe(neg ? -n : n), safe(d));
}
Rational Rational::operator+(const Rational &b) const {
  auto g = std::gcd(d_, b.d_);
  return {safe(__int128(n_) * (b.d_ / g) + __int128(b.n_) * (d_ / g)),
          safe(__int128(d_ / g) * b.d_)};
}
Rational Rational::operator-(const Rational &b) const {
  return *this + Rational(-b.n_, b.d_);
}
Rational Rational::operator*(const Rational &b) const {
  auto g = std::gcd(n_, b.d_), h = std::gcd(b.n_, d_);
  return {safe(__int128(n_ / g) * (b.n_ / h)), safe(__int128(d_ / h) * (b.d_ / g))};
}
Rational Rational::operator/(const Rational &b) const {
  require(b.n_ != 0, "division_by_zero", "Zero denominator");
  return *this * Rational(b.n_ > 0 ? b.d_ : -b.d_, b.n_ > 0 ? b.n_ : -b.n_);
}
std::int64_t Rational::ceil() const {
  return n_ / d_ + (n_ % d_ > 0 ? 1 : 0);
}
std::string Rational::display(int places) const {
  require(places >= 0 && places <= 12, "precision", "Invalid display precision");
  __int128 scale = 1;
  for (int i = 0; i < places; i++)
    scale *= 10;
  __int128 a = n_;
  if (a < 0)
    a = -a;
  auto scaled = (a * scale + d_ / 2) / d_;
  auto whole = scaled / scale, frac = scaled % scale;
  auto dec = [](__int128 v) {
    std::string s;
    do {
      s.insert(s.begin(), char('0' + v % 10));
      v /= 10;
    } while (v);
    return s;
  };
  std::string s = (n_ < 0 ? "-" : "") + dec(whole);
  if (places) {
    auto f = dec(frac);
    f.insert(0, static_cast<size_t>(places) - f.size(), '0');
    while (!f.empty() && f.back() == '0')
      f.pop_back();
    if (!f.empty())
      s += '.' + f;
  }
  return s;
}
Unit unit(const std::string &s) {
  static const std::map<std::string, Unit> u = {{"count", {"count", "count", 1}},
                                                {"token", {"token", "token", 1}},
                                                {"request/s", {"rate", "request/s", 1}},
                                                {"request/min", {"rate", "request/s", {1, 60}}},
                                                {"token/s", {"token_rate", "token/s", 1}},
                                                {"s", {"time", "s", 1}},
                                                {"ms", {"time", "s", {1, 1000}}},
                                                {"hour", {"time", "s", 3600}},
                                                {"day", {"time", "s", 86400}},
                                                {"ratio", {"ratio", "ratio", 1}},
                                                {"percent", {"ratio", "ratio", {1, 100}}},
                                                {"B", {"bytes", "B", 1}},
                                                {"GB", {"bytes", "B", 1000000000}},
                                                {"TB", {"bytes", "B", 1000000000000LL}},
                                                {"GiB", {"bytes", "B", 1073741824}},
                                                {"TiB", {"bytes", "B", 1099511627776LL}},
                                                {"PiB", {"bytes", "B", 1125899906842624LL}},
                                                {"B/s", {"byte_rate", "B/s", 1}},
                                                {"GB/s", {"byte_rate", "B/s", 1000000000}},
                                                {"GiB/s", {"byte_rate", "B/s", 1073741824}},
                                                {"Gbps", {"byte_rate", "B/s", 125000000}},
                                                {"ops/s", {"ops_rate", "ops/s", 1}}};
  auto it = u.find(s);
  require(it != u.end(), "unit", "Unsupported unit: " + s);
  return it->second;
}
std::optional<Rational> quantity(const Json &q, const std::string &dim, const std::string &path) {
  keys(q, {"state", "value", "unit", "origin", "source", "accepted", "reason", "active"}, path);
  auto state = text(q, "state", path);
  require(state == "known" || state == "estimated" || state == "assumed" || state == "unknown",
          "state", "Invalid observation state", path);
  if (q.contains("active"))
    require(q["active"].is_boolean(), "type", "active must be boolean", path);
  if (!q.value("active", true))
    return {};
  if (state == "unknown") {
    require(!q.contains("value"), "unknown_value", "Unknown must not contain a numeric value",
            path);
    return {};
  }
  auto u = unit(text(q, "unit", path));
  require(u.dimension == dim, "dimension", "Incompatible unit", path);
  auto r = Rational::decimal(text(q, "value", path)) * u.factor;
  require(r >= Rational(0), "negative", "Negative quantity", path);
  auto origin = text(q, "origin", path);
  require(origin == "customer" || origin == "measurement" || origin == "template" ||
              origin == "agent",
          "origin", "Invalid origin", path);
  require(!text(q, "source", path).empty() && text(q, "source", path).size() <= 2048, "source",
          "Source reference length must be 1–2048", path);
  if (q.contains("accepted"))
    require(q["accepted"].is_boolean(), "type", "accepted must be boolean", path);
  if (state == "assumed" && !q.value("accepted", false))
    return {};
  return r;
}
Json normalize_quantity(const Json &q, const std::string &path) {
  if (!q.value("active", true))
    return nullptr;
  if (q.value("state", "") == "unknown") {
    quantity(q, "count", path);
    return q;
  }
  auto u = unit(text(q, "unit", path));
  auto v = quantity(q, u.dimension, path);
  Json out = q;
  if (v) {
    // Recurring conversions (e.g. 100 requests/minute) cannot be written as
    // finite canonical decimals. Retain the original exact quantity and unit;
    // arithmetic still uses Rational. Never reject or round valid demand.
    auto canonical = v->display(12);
    if (Rational::decimal(canonical) == *v) {
      out["value"] = canonical;
      out["unit"] = u.canonical;
    }
  }
  return out;
}
} // namespace anubis
