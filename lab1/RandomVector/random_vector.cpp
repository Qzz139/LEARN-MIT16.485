#include "random_vector.h"

#include <cmath>
#include <cstdlib>
#include <stdexcept>

RandomVector::RandomVector(int size, double max_val) {
  if (size <= 0 || !std::isfinite(max_val) || max_val < 0.0) {
    throw std::invalid_argument("size must be positive and max_val finite and nonnegative");
  }

  vect.reserve(static_cast<std::size_t>(size));
  for (int i = 0; i < size; ++i) {
    const double unit = static_cast<double>(std::rand()) / RAND_MAX;
    vect.push_back(unit * max_val);
  }
}

void RandomVector::print() {
  for (std::size_t i = 0; i < vect.size(); ++i) {
    if (i != 0) std::cout << ' ';
    std::cout << vect[i];
  }
  std::cout << '\n';
}

double RandomVector::mean() {
  double sum = 0.0;
  for (double value : vect) sum += value;
  return sum / vect.size();
}

double RandomVector::max() {
  double result = vect[0];
  for (double value : vect) {
    if (value > result) result = value;
  }
  return result;
}

double RandomVector::min() {
  double result = vect[0];
  for (double value : vect) {
    if (value < result) result = value;
  }
  return result;
}

void RandomVector::printHistogram(int bins) {
  if (bins <= 0) throw std::invalid_argument("bins must be positive");

  std::vector<int> counts(static_cast<std::size_t>(bins), 0);
  const double low = min();
  const double high = max();
  if (low == high) {
    counts[0] = static_cast<int>(vect.size());
  } else {
    for (double value : vect) {
      // Left-closed bins; the maximum belongs to the final bin.
      int index = static_cast<int>((value - low) / (high - low) * bins);
      if (index >= bins) index = bins - 1;
      ++counts[static_cast<std::size_t>(index)];
    }
  }

  int tallest = 0;
  for (int count : counts) {
    if (count > tallest) tallest = count;
  }
  for (int level = tallest; level > 0; --level) {
    for (int bin = 0; bin < bins; ++bin) {
      if (bin != 0) std::cout << ' ';
      std::cout << (counts[static_cast<std::size_t>(bin)] >= level ? "***" : "   ");
    }
    std::cout << '\n';
  }
}
