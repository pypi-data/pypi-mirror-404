#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "sdfg::sdfgopt" for configuration "Release"
set_property(TARGET sdfg::sdfgopt APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(sdfg::sdfgopt PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib64/libsdfgopt.a"
  )

list(APPEND _cmake_import_check_targets sdfg::sdfgopt )
list(APPEND _cmake_import_check_files_for_sdfg::sdfgopt "${_IMPORT_PREFIX}/lib64/libsdfgopt.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
