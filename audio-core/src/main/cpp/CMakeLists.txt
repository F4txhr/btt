# For more information about using CMake with Android Studio, read the
cmake_minimum_required(VERSION 3.22.1)

project("audioplayer-core")

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Oboe
find_library(oboe_lib oboe)

# Include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

# Source files
set(SOURCES
    audio_engine.cpp
    dsp_processor.cpp
    equalizer.cpp
    visualizer.cpp
    audio_player_jni.cpp
)

# Create shared library
add_library(audioplayer-core SHARED ${SOURCES})

# Link libraries
target_link_libraries(audioplayer-core
    ${oboe_lib}
    android
    log
)

# Compiler flags
target_compile_options(audioplayer-core PRIVATE
    -Wall
    -Wextra
    -O3
    -ffast-math
    -march=native
)
