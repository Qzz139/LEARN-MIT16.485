cmake_minimum_required(VERSION 3.10)
project(lab1_cmake_example LANGUAGES CXX)

add_library(message message.cpp)
target_compile_features(message PUBLIC cxx_std_11)

add_executable(example main.cpp)
target_link_libraries(example PRIVATE message)
