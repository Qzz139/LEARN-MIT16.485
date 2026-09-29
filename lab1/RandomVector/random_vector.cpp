#include "random_vector.h"

#include <cstdlib>

// Fill the vector with `size` random numbers in [0, max_val].
RandomVector::RandomVector(int size, double max_val) {
  for (int i = 0; i < size; ++i) {
    // Cast to double first: rand() / RAND_MAX would be integer division (almost always 0).
    double unit = static_cast<double>(std::rand()) / RAND_MAX;  // in [0, 1]
    vect.push_back(unit * max_val);
  }
}

void RandomVector::print() {
  for (std::size_t i = 0; i < vect.size(); ++i) {
    if (i > 0) std::cout << ' ';
    std::cout << vect[i];
  }
  std::cout << '\n';
}

double RandomVector::mean() {
  double sum = 0.0;
  for (double value : vect) sum += value;
  return sum / vect.size();
}

// max() and min() start from the first element, not from an arbitrary constant like 0.
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
  // Step 1: count how many values fall in each of `bins` equal-width bins over [min, max].
  std::vector<int> counts(bins, 0);
  double low = min(), high = max();
  for (double value : vect) {
    int index = 0;  // if every value is equal (high == low), all go to the first bin
    if (high > low) index = static_cast<int>((value - low) / (high - low) * bins);
    // Bins are [left, right); the maximum itself gives index == bins, so move it
    // into the last bin instead of writing past the end of `counts`.
    if (index == bins) index = bins - 1;
    ++counts[index];
  }

  // Step 2: print the columns from the top row down. A bin gets "***" in every
  // row whose level is at most its count.
  int tallest = 0;
  for (int count : counts) {
    if (count > tallest) tallest = count;
  }
  for (int level = tallest; level > 0; --level) {
    for (int bin = 0; bin < bins; ++bin) {
      if (bin > 0) std::cout << ' ';
      std::cout << (counts[bin] >= level ? "***" : "   ");
    }
    std::cout << '\n';
  }
}
