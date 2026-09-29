// A few checks for RandomVector. Any failed assert stops the program,
// so the final "passed" line is printed only if every check held.
#include <cassert>
#include <cstdlib>
#include <iostream>
#include <sstream>
#include <string>

#include "random_vector.h"

// printHistogram() only prints, so temporarily redirect std::cout into a string.
std::string histogram(RandomVector& rv, int bins) {
  std::ostringstream out;
  std::streambuf* old = std::cout.rdbuf(out.rdbuf());
  rv.printHistogram(bins);
  std::cout.rdbuf(old);
  return out.str();
}

// Every "***" stands for one value in one bin.
int countStars(const std::string& text) {
  int n = 0;
  std::size_t pos = text.find("***");
  while (pos != std::string::npos) {
    ++n;
    pos = text.find("***", pos + 3);
  }
  return n;
}

int main() {
  std::srand(314159);  // same seed as main.cpp
  RandomVector rv(20);
  assert(0.0 <= rv.min() && rv.min() <= rv.mean() && rv.mean() <= rv.max() && rv.max() <= 1.0);

  // No value may be lost or counted twice, including the maximum.
  assert(countStars(histogram(rv, 5)) == 20);
  assert(countStars(histogram(rv, 1)) == 20);
  assert(countStars(histogram(rv, 30)) == 20);  // more bins than values

  // All values equal (max == min): no division by zero, everything in the first bin.
  RandomVector zero(3, 0.0);
  assert(zero.min() == 0.0 && zero.mean() == 0.0 && zero.max() == 0.0);
  assert(histogram(zero, 2) == "***    \n***    \n***    \n");

  std::cout << "All RandomVector checks passed: range, mean, 20 stars for 1/5/30 bins, equal values\n";
}
