# For more information about using CMake with Android Studio, read the
cmake_minimum_required(VERSION 3.22.1)

project("audioplayerpro")

# Add the Oboe package.
# This will find the Oboe library that was downloaded by Gradle.
find_package(oboe REQUIRED)

add_library(
        audiocore-native
        SHARED
        native-lib.cpp)

find_library(
        log-lib
        log)

# Link the Oboe and log libraries to our native library.
target_link_libraries(
        audiocore-native
        oboe::oboe
        ${log-lib})
