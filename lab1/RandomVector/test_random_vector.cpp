#include "random_vector.h"

#include <cassert>
#include <cmath>
#include <cstdlib>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

std::vector<int> histogram(RandomVector& rv, int bins) {
  std::ostringstream output;
  std::streambuf* previous = std::cout.rdbuf(output.rdbuf());
  rv.printHistogram(bins);
  std::cout.rdbuf(previous);

  std::vector<int> counts(static_cast<std::size_t>(bins), 0);
  std::istringstream rows(output.str());
  std::string row;
  while (std::getline(rows, row)) {
    assert(row.size() == static_cast<std::size_t>(4 * bins - 1));
    for (int bin = 0; bin < bins; ++bin) {
      const std::string cell = row.substr(static_cast<std::size_t>(4 * bin), 3);
      assert(cell == "***" || cell == "   ");
      if (cell == "***") ++counts[static_cast<std::size_t>(bin)];
    }
  }
  return counts;
}

int main() {
  std::srand(314159);
  RandomVector rv(20);
  const double low = rv.min();
  const double high = rv.max();
  const double average = rv.mean();
  assert(0.0 <= low && low <= average && average <= high && high <= 1.0);

  std::ostringstream printed;
  std::streambuf* previous = std::cout.rdbuf(printed.rdbuf());
  rv.print();
  std::cout.rdbuf(previous);
  std::istringstream values(printed.str());
  double printed_value = 0.0;
  int printed_count = 0;
  while (values >> printed_value) {
    assert(0.0 <= printed_value && printed_value <= 1.0);
    ++printed_count;
  }
  assert(printed_count == 20);

  // Recreate the seeded input, then classify it by comparisons with bin edges.
  std::srand(314159);
  double sum = 0.0;
  std::vector<int> expected(5, 0);
  for (int i = 0; i < 20; ++i) {
    const double value = static_cast<double>(std::rand()) / RAND_MAX;
    sum += value;
    int bin = 4;
    for (int edge = 1; edge < 5; ++edge) {
      if (value < low + (high - low) * edge / 5) {
        bin = edge - 1;
        break;
      }
    }
    ++expected[static_cast<std::size_t>(bin)];
  }
  assert(std::fabs(average - sum / 20) < 1e-12);
  assert(histogram(rv, 5) == expected);

  std::srand(1);
  RandomVector singleton(1);
  assert(singleton.min() == singleton.max());
  assert(singleton.mean() == singleton.min());
  assert((histogram(singleton, 5) == std::vector<int>{1, 0, 0, 0, 0}));
  assert((histogram(singleton, 1) == std::vector<int>{1}));

  RandomVector zero(3, 0.0);
  assert(zero.mean() == 0.0 && zero.min() == 0.0 && zero.max() == 0.0);
  assert((histogram(zero, 5) == std::vector<int>{3, 0, 0, 0, 0}));
  RandomVector scaled(10, 2.0);
  assert(0.0 <= scaled.min() && scaled.max() <= 2.0);
  assert((histogram(rv, 1) == std::vector<int>{20}));
  std::vector<int> many = histogram(singleton, 8);
  assert((many == std::vector<int>{1, 0, 0, 0, 0, 0, 0, 0}));

  bool rejected_size = false, rejected_max = false;
  bool rejected_nonfinite = false, rejected_bins = false;
  try { RandomVector bad(0); } catch (const std::invalid_argument&) { rejected_size = true; }
  try { RandomVector bad(2, -1.0); } catch (const std::invalid_argument&) { rejected_max = true; }
  try { RandomVector bad(2, std::numeric_limits<double>::infinity()); }
  catch (const std::invalid_argument&) { rejected_nonfinite = true; }
  try { rv.printHistogram(0); } catch (const std::invalid_argument&) { rejected_bins = true; }
  assert(rejected_size && rejected_max && rejected_nonfinite && rejected_bins);

  std::cout << "Default: 20 values, 5 bins, counts =";
  for (int count : expected) std::cout << ' ' << count;
  std::cout << "; total = 20\n";
  std::cout << "Boundary cases: singleton, zero maximum, scaled maximum, one bin, eight bins: PASS\n";
  std::cout << "Invalid parameters: zero size, negative/nonfinite maximum, zero bins: PASS\n";
}
