cmake_minimum_required(VERSION 3.15)

# Discover VCPKG toolchain
if (NOT DEFINED CMAKE_TOOLCHAIN_FILE)
  # VCPKG_ROOT is what Microsoft recommends,
  # VCPKG_INSTALLATION_ROOT is what's defined on Azure
  if(DEFINED ENV{VCPKG_ROOT})
    set(CMAKE_TOOLCHAIN_FILE
        "$ENV{VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake"
        CACHE STRING "")
  elseif(DEFINED ENV{VCPKG_INSTALLATION_ROOT})
    set(CMAKE_TOOLCHAIN_FILE
        "$ENV{VCPKG_INSTALLATION_ROOT}/scripts/buildsystems/vcpkg.cmake"
        CACHE STRING "")
  endif()
endif()

# For native builds where vcpkg toolchain incorrectly triggers cross-compilation detection
message("VCPKG_TARGET_TRIPLET=${VCPKG_TARGET_TRIPLET}, CMAKE_HOST_SYSTEM_PROCESSOR=${CMAKE_HOST_SYSTEM_PROCESSOR}")
if(VCPKG_TARGET_TRIPLET MATCHES "arm64-osx" AND CMAKE_HOST_SYSTEM_PROCESSOR STREQUAL "arm64")
    # Point to where vcpkg will install Qt tools
    set(QT_HOST_PATH "${VCPKG_INSTALLED_DIR}/${VCPKG_TARGET_TRIPLET}" CACHE PATH "Qt host tools path")
    message("QT_HOST_PATH=${QT_HOST_PATH}")
endif()

file(READ "${CMAKE_CURRENT_SOURCE_DIR}/version.txt" PROCGEN_VERSION)
string(STRIP "${PROCGEN_VERSION}" PROCGEN_VERSION)

project(gymnasium_procgen VERSION ${PROCGEN_VERSION} LANGUAGES CXX)

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
