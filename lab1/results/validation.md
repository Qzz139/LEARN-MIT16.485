# Lab 1 C++ verification for the report

Environment: Ubuntu 20.04.6 LTS on WSL 2, x86_64, `g++ 9.4.0`. The MIT [warm-up and RandomVector exercise](https://vnav.mit.edu/labs_2023/lab1/exercises.html) supplies the question set and the template contract. Local course scoring assigns 25 points to each of these two parts.

## C++ warm-up

All ten answers are in [`../cpp-warmup.txt`](../cpp-warmup.txt), grouped as 2 operator, 4 reference/pointer, and 4 numeric-type questions. [`cpp_warmup_check.cpp`](cpp_warmup_check.cpp) runs the relevant snippets. It compiled with `g++ -std=c++11 -Wall -Wextra -pedantic` without warnings; the [Ubuntu output](cpp_warmup_check.txt) confirms `i=2, j=1`, `b`, `10 10`, `1764`, `0`, `0`, `3`, `255`, and `0`. This environment measured `sizeof(short,int,long,long long) = 2,4,8,8` and `sizeof(float,double) = 4,8`; these sizes are platform measurements rather than universal byte counts.

## RandomVector

The [original class interface](../RandomVector/random_vector.h) and [default entry point](../RandomVector/main.cpp) remain intact. [`random_vector.cpp`](../RandomVector/random_vector.cpp) implements constructor, `print`, `mean`, `min`, `max`, and `printHistogram` with basic loops and no `<algorithm>` functions.

With seed `314159`, the default 20 values on this Ubuntu system have mean `0.55804`, min `0.0278694`, and max `0.982655`. The five histogram counts are `5, 1, 4, 3, 7`; their sum is 20. The complete [program output](random_vector.txt) includes the vertical histogram. The numerical sequence differs from the MIT webpage example and the local macOS run because C libraries need not use the same `std::rand()` sequence; a fixed seed guarantees repeatability only within the same implementation.

[`test_random_vector.cpp`](../RandomVector/test_random_vector.cpp) checks `0 <= min <= mean <= max <= 1`, counts the `***` cells to confirm that 1, 5 and 30 bins all hold exactly 20 values (so the maximum is not lost), and checks that three equal values all go to the first bin. The [Ubuntu test output](random_vector_validation.txt) reports all checks passed. Regular bins are left-closed/right-open and the last bin includes the maximum.

Report figures are [`04_cpp_warmup.png`](figures/04_cpp_warmup.png) and [`05_random_vector.png`](figures/05_random_vector.png). They render live SSH/WSL output and are labeled as such; they are not desktop-window screenshots. Each has an adjacent `.txt` transcript.
