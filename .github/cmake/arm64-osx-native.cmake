set(VCPKG_TARGET_ARCHITECTURE arm64)
set(VCPKG_CRT_LINKAGE dynamic)
set(VCPKG_LIBRARY_LINKAGE static)
set(VCPKG_CMAKE_SYSTEM_NAME Darwin)

# Force native compilation detection
set(VCPKG_CMAKE_CONFIGURE_OPTIONS
    -DCMAKE_CROSSCOMPILING=FALSE
    -DQT_BUILD_TOOLS_WHEN_CROSS_COMPILING=ON
)

# Ensure host and target triplets match for Qt tools
set(VCPKG_HOST_TRIPLET arm64-osx-native)
