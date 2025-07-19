cmake_minimum_required(VERSION 3.15)

# Set cmake module path
set(CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/cmake ${CMAKE_MODULE_PATH})

# Overlay VCPKG custom triplets
if(NOT DEFINED VCPKG_OVERLAY_TRIPLETS)
  set(VCPKG_OVERLAY_TRIPLETS
      "${CMAKE_MODULE_PATH}"
      CACHE STRING "")
endif()

# Discover VCPKG default triplet
if(DEFINED ENV{VCPKG_DEFAULT_TRIPLET} AND NOT DEFINED VCPKG_TARGET_TRIPLET)
  message(status "ENV{VCPKG_DEFAULT_TRIPLET}=$ENV{VCPKG_DEFAULT_TRIPLET}")
  set(VCPKG_TARGET_TRIPLET
      "$ENV{VCPKG_DEFAULT_TRIPLET}"
      CACHE STRING "")
endif()

message(status "CMAKE_MODULE_PATH=${CMAKE_MODULE_PATH}, VCPKG_OVERLAY_TRIPLETS=${VCPKG_OVERLAY_TRIPLETS}, ${VCPKG_TARGET_TRIPLET}")

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

# Don't allow running cmake in root directory
if (CMAKE_BINARY_DIR STREQUAL CMAKE_SOURCE_DIR)
  message(FATAL_ERROR [=[
    Source and build directories cannot be the same.
    You should probably also remove CMakeFiles/ and CMakeCache.txt.
  ]=])
endif()


file(READ "${CMAKE_CURRENT_SOURCE_DIR}/version.txt" PROCGEN_VERSION)
string(STRIP "${PROCGEN_VERSION}" PROCGEN_VERSION)

project(gymnasium_procgen VERSION ${PROCGEN_VERSION} LANGUAGES CXX)

message("VCPKG_OVERLAY_TRIPLETS=${VCPKG_OVERLAY_TRIPLETS}")
message("CMAKE_CROSSCOMPILING=${CMAKE_CROSSCOMPILING}")

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
