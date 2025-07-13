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

# NOW vcpkg variables are available - debug the cross-compilation detection
message(STATUS "=== DEBUGGING QT CROSS-COMPILATION ISSUE ===")
message(STATUS "CMAKE_CROSSCOMPILING: ${CMAKE_CROSSCOMPILING}")
message(STATUS "CMAKE_SYSTEM_NAME: ${CMAKE_SYSTEM_NAME}")
message(STATUS "CMAKE_HOST_SYSTEM_NAME: ${CMAKE_HOST_SYSTEM_NAME}")
message(STATUS "CMAKE_SYSTEM_PROCESSOR: ${CMAKE_SYSTEM_PROCESSOR}")
message(STATUS "CMAKE_HOST_SYSTEM_PROCESSOR: ${CMAKE_HOST_SYSTEM_PROCESSOR}")
message(STATUS "VCPKG_TARGET_TRIPLET: ${VCPKG_TARGET_TRIPLET}")
message(STATUS "VCPKG_INSTALLED_DIR: ${VCPKG_INSTALLED_DIR}")
message(STATUS "============================================")

# Check if this is native compilation being misdetected as cross-compilation
if(CMAKE_CROSSCOMPILING AND
   CMAKE_SYSTEM_NAME STREQUAL CMAKE_HOST_SYSTEM_NAME AND
   CMAKE_SYSTEM_PROCESSOR STREQUAL CMAKE_HOST_SYSTEM_PROCESSOR)
    message(STATUS "Detected native compilation misidentified as cross-compilation")
    # Tell Qt to build tools when cross-compiling (even though we're not really cross-compiling)
    set(QT_BUILD_TOOLS_WHEN_CROSS_COMPILING ON CACHE BOOL "Build Qt tools during cross-compilation")
    message(STATUS "Set QT_BUILD_TOOLS_WHEN_CROSS_COMPILING=ON")
elseif(CMAKE_CROSSCOMPILING)
    message(STATUS "Actual cross-compilation detected - setting QT_HOST_PATH")
    set(QT_HOST_PATH "${VCPKG_INSTALLED_DIR}/${VCPKG_HOST_TRIPLET}" CACHE PATH "Qt host tools path")
    message(STATUS "QT_HOST_PATH: ${QT_HOST_PATH}")
else()
    message(STATUS "Native compilation correctly detected")
endif()

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
