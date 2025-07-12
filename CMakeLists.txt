# ROOT CMakeLists.txt
cmake_minimum_required(VERSION 3.15)
project(gymnasium_procgen VERSION 1.0.0 LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Global compiler settings
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(CMAKE_CXX_VISIBILITY_PRESET hidden)

# Build type defaults
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Find dependencies
find_package(Qt6 REQUIRED COMPONENTS Core Gui)

# Platform-specific compiler flags
if(APPLE)
    add_compile_options(-ferror-limit=1)
    add_compile_options(-Werror -Wextra -Wshadow -Wall -Wformat=2 -Wundef -Wvla
                       -Wmissing-include-dirs -Wnon-virtual-dtor -Wno-unused-parameter)
endif()

if(MSVC)
    add_compile_definitions(_CRT_SECURE_NO_WARNINGS)
endif()

# Optimization flags
if(APPLE OR UNIX)
    if(CMAKE_BUILD_TYPE STREQUAL "Release")
        if(PROCGEN_PACKAGE)
            add_compile_options(-march=ivybridge)
        else()
            add_compile_options(-march=native)
        endif()
    endif()
    add_compile_options(-fno-omit-frame-pointer)
endif()

# Collect all source files from gymnasium_procgen/src
file(GLOB_RECURSE SOURCES
    "gymnasium_procgen/src/*.cpp"
    "gymnasium_procgen/src/*.h"
)

# Create the shared library
add_library(procgen_env SHARED ${SOURCES})

# Set target properties - Install to gymnasium_procgen package directory
set_target_properties(procgen_env PROPERTIES
    OUTPUT_NAME "env"
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/gymnasium_procgen
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/gymnasium_procgen
)

# Include directories
target_include_directories(procgen_env
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/gymnasium_procgen/src
)

# Link libraries
target_link_libraries(procgen_env
    PRIVATE
        Qt6::Core
        Qt6::Gui
)

# Install the library to the Python package directory
install(TARGETS procgen_env
    LIBRARY DESTINATION gymnasium_procgen
    RUNTIME DESTINATION gymnasium_procgen
)
