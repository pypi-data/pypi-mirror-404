#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "sdfg::sdfgrpc" for configuration "Release"
set_property(TARGET sdfg::sdfgrpc APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(sdfg::sdfgrpc PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib64/libsdfgrpc.a"
  )

list(APPEND _cmake_import_check_targets sdfg::sdfgrpc )
list(APPEND _cmake_import_check_files_for_sdfg::sdfgrpc "${_IMPORT_PREFIX}/lib64/libsdfgrpc.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
