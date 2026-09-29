# Lab 1 RandomVector

The class interface and default `main.cpp` come from the [MIT VNAV Lab 1 template](https://github.com/MIT-SPARK/VNAV-labs/tree/master/lab1), accessed on 2026-09-24. The six methods in `random_vector.cpp` complete the template without functions from `<algorithm>`.

Build and run on Ubuntu 20.04 from this directory:

```sh
g++ -std=c++11 -Wall -Wextra -pedantic -o random_vector main.cpp random_vector.cpp
./random_vector
g++ -std=c++11 -Wall -Wextra -pedantic -o test_random_vector test_random_vector.cpp random_vector.cpp
./test_random_vector
```

`test_random_vector.cpp` checks that `min <= mean <= max`, that the histogram keeps all 20 values (for 1, 5 and 30 bins), and that equal values all land in the first bin. Bins are left-closed and right-open, except that the final bin includes the maximum. There is no input validation: the program assumes a positive size and bin count, as the lab does. The fixed seed in `main.cpp` makes runs repeatable on the same C library; `std::rand()` sequences can differ across platforms.
