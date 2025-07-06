# Find Qt
find_package(Qt6 COMPONENTS Core Gui QUIET)
if(Qt6_FOUND)
    set(QT_VERSION_MAJOR 6)
    message(STATUS "Found Qt6: ${Qt6_VERSION}")
else()
    find_package(Qt5 COMPONENTS Core Gui REQUIRED)
    set(QT_VERSION_MAJOR 5)
    message(STATUS "Found Qt5: ${Qt5_VERSION}")
endif()

# Find gym3
find_package(PkgConfig QUIET)
if(PkgConfig_FOUND)
    pkg_check_modules(GYM3 QUIET gym3)
endif()

# If not found via pkg-config, try to find gym3 manually
if(NOT GYM3_FOUND)
    find_path(GYM3_INCLUDE_DIR
        NAMES libenv.h
        PATHS
            ${CMAKE_CURRENT_SOURCE_DIR}/../gym3/libenv
            /usr/local/include/gym3
            /usr/include/gym3
    )

    if(GYM3_INCLUDE_DIR)
        set(GYM3_FOUND TRUE)
        set(GYM3_INCLUDE_DIRS ${GYM3_INCLUDE_DIR})
        message(STATUS "Found gym3 include dir: ${GYM3_INCLUDE_DIR}")
    else()
        message(FATAL_ERROR "Could not find gym3. Please install gym3 or set GYM3_INCLUDE_DIR")
    endif()
endif()
