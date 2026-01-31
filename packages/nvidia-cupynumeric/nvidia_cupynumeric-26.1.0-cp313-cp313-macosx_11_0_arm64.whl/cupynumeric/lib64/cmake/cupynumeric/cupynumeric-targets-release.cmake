#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "cupynumeric::cupynumeric" for configuration "Release"
set_property(TARGET cupynumeric::cupynumeric APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(cupynumeric::cupynumeric PROPERTIES
  IMPORTED_LINK_DEPENDENT_LIBRARIES_RELEASE "tblis"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib64/libcupynumeric.dylib"
  IMPORTED_SONAME_RELEASE "@rpath/libcupynumeric.dylib"
  )

list(APPEND _cmake_import_check_targets cupynumeric::cupynumeric )
list(APPEND _cmake_import_check_files_for_cupynumeric::cupynumeric "${_IMPORT_PREFIX}/lib64/libcupynumeric.dylib" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
