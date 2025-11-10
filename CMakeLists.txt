cmake_minimum_required(VERSION 3.18)

# On macOS, ensure we build for the correct architecture
# This must be set BEFORE the project() command
if(APPLE AND NOT DEFINED CMAKE_OSX_ARCHITECTURES)
    # If not explicitly set by cibuildwheel, use the native architecture
    execute_process(
        COMMAND uname -m
        OUTPUT_VARIABLE NATIVE_ARCH
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )
    set(CMAKE_OSX_ARCHITECTURES "${NATIVE_ARCH}" CACHE STRING "Target architectures" FORCE)
endif()

project(gymnasium_procgen LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# MSVC-specific: Qt6 requires /Zc:__cplusplus to properly report C++17
# and /permissive- for standards conformance
if(MSVC)
    add_compile_options(/Zc:__cplusplus /permissive-)
endif()

# Position independent code is required for Python modules
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Find Qt6 components - only Core and Gui (headless)
# Qt6 should be provided by the system or built separately
find_package(Qt6 REQUIRED COMPONENTS Core Gui)

# Enable Qt6 minimal headless mode
# This tells Qt to use the offscreen platform plugin
add_compile_definitions(QT_QPA_PLATFORM=offscreen)

# Collect all source files
set(PROCGEN_SOURCES
    # Core sources
    gymnasium_procgen/src/assetgen.cpp
    gymnasium_procgen/src/basic-abstract-game.cpp
    gymnasium_procgen/src/cpp-utils.cpp
    gymnasium_procgen/src/entity.cpp
    gymnasium_procgen/src/game-registry.cpp
    gymnasium_procgen/src/game.cpp
    gymnasium_procgen/src/mazegen.cpp
    gymnasium_procgen/src/randgen.cpp
    gymnasium_procgen/src/resources.cpp
    gymnasium_procgen/src/roomgen.cpp
    gymnasium_procgen/src/vecgame.cpp
    gymnasium_procgen/src/vecoptions.cpp

    # Game implementations
    gymnasium_procgen/src/games/bigfish.cpp
    gymnasium_procgen/src/games/bossfight.cpp
    gymnasium_procgen/src/games/caveflyer.cpp
    gymnasium_procgen/src/games/chaser.cpp
    gymnasium_procgen/src/games/climber.cpp
    gymnasium_procgen/src/games/coinrun.cpp
    gymnasium_procgen/src/games/coinrun_old.cpp
    gymnasium_procgen/src/games/dodgeball.cpp
    gymnasium_procgen/src/games/fruitbot.cpp
    gymnasium_procgen/src/games/heist.cpp
    gymnasium_procgen/src/games/jumper.cpp
    gymnasium_procgen/src/games/leaper.cpp
    gymnasium_procgen/src/games/maze.cpp
    gymnasium_procgen/src/games/miner.cpp
    gymnasium_procgen/src/games/ninja.cpp
    gymnasium_procgen/src/games/plunder.cpp
    gymnasium_procgen/src/games/starpilot.cpp
)

# Create the shared library (libenv.so / libenv.dylib / env.dll)
add_library(env SHARED ${PROCGEN_SOURCES})

# Set the output name to match what the Python code expects
set_target_properties(env PROPERTIES
    PREFIX "lib"
    OUTPUT_NAME "env"
)

# Platform-specific library naming
if(WIN32)
    set_target_properties(env PROPERTIES
        PREFIX ""
        SUFFIX ".dll"
    )
elseif(APPLE)
    set_target_properties(env PROPERTIES
        SUFFIX ".dylib"
    )
else()
    set_target_properties(env PROPERTIES
        SUFFIX ".so"
    )
endif()

# Include directories
target_include_directories(env PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/gymnasium_procgen/src
)

# Link Qt6 libraries
target_link_libraries(env PRIVATE
    Qt6::Core
    Qt6::Gui
)

# Platform-specific settings
if(APPLE)
    # On macOS, ensure we use libc++ and appropriate deployment target
    target_compile_options(env PRIVATE -stdlib=libc++)
    set_target_properties(env PROPERTIES
        MACOSX_RPATH ON
        INSTALL_RPATH "@loader_path"
    )
elseif(UNIX)
    # On Linux, set RPATH for bundled Qt libraries
    set_target_properties(env PROPERTIES
        INSTALL_RPATH "$ORIGIN"
    )
endif()

# Windows-specific settings
if(WIN32)
    # Ensure proper DLL exports
    target_compile_definitions(env PRIVATE
        _CRT_SECURE_NO_WARNINGS
    )
endif()

# Install the library to the gymnasium_procgen package directory
install(TARGETS env
    LIBRARY DESTINATION gymnasium_procgen
    RUNTIME DESTINATION gymnasium_procgen
)

# Install Qt6 plugins for headless rendering
# This ensures the offscreen platform plugin is available
if(Qt6_FOUND)
    # Get Qt6 plugin directory
    get_target_property(QT_QMAKE_EXECUTABLE Qt6::qmake IMPORTED_LOCATION)
    execute_process(
        COMMAND "${QT_QMAKE_EXECUTABLE}" -query QT_INSTALL_PLUGINS
        OUTPUT_VARIABLE QT_PLUGINS_DIR
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )

    # Install the offscreen platform plugin
    if(EXISTS "${QT_PLUGINS_DIR}/platforms")
        install(DIRECTORY "${QT_PLUGINS_DIR}/platforms"
            DESTINATION gymnasium_procgen/qt6_plugins
            FILES_MATCHING
            PATTERN "*offscreen*"
            PATTERN "*minimal*"
        )
    endif()
endif()
