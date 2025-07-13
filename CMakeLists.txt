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

# Rest of your CMakeLists.txt remains the same...
