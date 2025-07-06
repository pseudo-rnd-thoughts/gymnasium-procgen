# Collect all source files
file(GLOB_RECURSE SOURCES
    "*.cpp"
    "*.h"
)

# Create the shared library
add_library(procgen_env SHARED ${SOURCES})

# Set target properties
set_target_properties(procgen_env PROPERTIES
    OUTPUT_NAME "env"
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/procgen
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/procgen
)

# Include directories
target_include_directories(procgen_env
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${GYM3_INCLUDE_DIRS}
)

# include qt6
find_package(Qt6 COMPONENTS Core Gui REQUIRED)

# target_link_libraries(env Qt6::Core Qt6::Gui)

# Link libraries
target_link_libraries(procgen_env
    PRIVATE
        Qt6::Core
        Qt6::Gui
)

# Compiler-specific options
if(APPLE)
    target_compile_options(procgen_env PRIVATE
        -ferror-limit=1
        -Werror -Wextra -Wshadow -Wall -Wformat=2 -Wundef -Wvla
        -Wmissing-include-dirs -Wnon-virtual-dtor -Wno-unused-parameter
    )

    if(CMAKE_BUILD_TYPE STREQUAL "Release")
        target_compile_options(procgen_env PRIVATE -march=ivybridge)
    endif()
endif()

if(UNIX AND NOT APPLE)
    if(CMAKE_BUILD_TYPE STREQUAL "Release")
        target_compile_options(procgen_env PRIVATE -march=native)
    endif()
    target_compile_options(procgen_env PRIVATE -fno-omit-frame-pointer)
endif()

if(MSVC)
    target_compile_definitions(procgen_env PRIVATE _CRT_SECURE_NO_WARNINGS)
endif()

# Install the library
install(TARGETS procgen_env
    LIBRARY DESTINATION procgen
    RUNTIME DESTINATION procgen
)
