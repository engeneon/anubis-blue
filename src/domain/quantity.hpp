#pragma once
#include "domain/json.hpp"
#include <cstdint>
#include <optional>
namespace anubis {
class Rational {
  std::int64_t n_ = 0, d_ = 1;

public:
  Rational(std::int64_t n = 0, std::int64_t d = 1);
  static Rational decimal(const std::string &value);
  std::int64_t num() const {
    return n_;
  }
  std::int64_t den() const {
    return d_;
  }
  Rational operator+(const Rational &) const;
  Rational operator-(const Rational &) const;
  Rational operator*(const Rational &) const;
  Rational operator/(const Rational &) const;
  auto operator<=>(const Rational &b) const {
    return (__int128(n_) * b.d_) <=> (__int128(b.n_) * d_);
  }
  bool operator==(const Rational &b) const {
    return n_ == b.n_ && d_ == b.d_;
  }
  std::int64_t ceil() const;
  std::string display(int decimals = 6) const;
  Json exact() const {
    return {{"numerator", std::to_string(n_)}, {"denominator", std::to_string(d_)}};
  }
};
struct Unit {
  std::string dimension, canonical;
  Rational factor;
};
Unit unit(const std::string &name);
std::optional<Rational> quantity(const Json &q, const std::string &dimension,
                                 const std::string &path);
Json normalize_quantity(const Json &q, const std::string &path);
} // namespace anubis
