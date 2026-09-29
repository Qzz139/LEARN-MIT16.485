// Runs the ten C++ warm-up snippets from ../cpp-warmup.txt and prints each result.
// The labels O1-O2 (operators), R1-R4 (references/pointers), N1-N4 (numeric types)
// match the question numbers.
#include <iostream>

void reset(int& value) { value = 0; }

int main() {
  int i = 0, j;
  j = ++i;
  j = i++;
  std::cout << "O1 i=" << i << " j=" << j << '\n';

  i = 42;
  std::cout << "O2 " << ((i < 42) ? "a" : "b") << '\n';

  int original;
  int& alias = original;
  original = 5;
  alias = 10;
  std::cout << "R1 " << original << ' ' << alias << '\n';

  int pointed = 42;
  int* pointer = &pointed;
  *pointer = *pointer**pointer;
  std::cout << "R2 " << *pointer << '\n';

  int values[4] = {42, 24, 42, 24};
  *(values + 2) = *(values + 1) - values[3];
  std::cout << "R3 " << *(values + 2) << '\n';

  j = 42;
  reset(j);
  std::cout << "R4 " << j << '\n';

  std::cout << "N1 sizeof(short,int,long,long long)="
            << sizeof(short) << ',' << sizeof(int) << ','
            << sizeof(long) << ',' << sizeof(long long) << '\n';
  std::cout << "N2 sizeof(float,double)=" << sizeof(float) << ','
            << sizeof(double) << " i=" << static_cast<int>(3.14) << '\n';
  unsigned char c = -1;
  std::cout << "N3 c=" << static_cast<unsigned int>(c) << '\n';
  i = 42;
  if (i) i = 0;
  else i = 43;
  std::cout << "N4 i=" << i << '\n';
}
