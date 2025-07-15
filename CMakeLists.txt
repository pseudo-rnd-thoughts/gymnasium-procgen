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

# Overlay VCPKG custom triplets
message("!!!!!!!!!! VCPKG_OVERLAY_TRIPLETS=${VCPKG_OVERLAY_TRIPLETS}")
if(NOT DEFINED VCPKG_OVERLAY_TRIPLETS)
  set(VCPKG_OVERLAY_TRIPLETS
      "${CMAKE_CURRENT_SOURCE_DIR}"
      CACHE STRING "")
endif()
message("!!!!!!!!!! VCPKG_OVERLAY_TRIPLETS=${VCPKG_OVERLAY_TRIPLETS}")

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
