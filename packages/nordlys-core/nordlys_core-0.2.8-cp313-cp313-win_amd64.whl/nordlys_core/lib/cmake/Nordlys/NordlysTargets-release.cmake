#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "Nordlys::nordlys_scoring" for configuration "Release"
set_property(TARGET Nordlys::nordlys_scoring APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(Nordlys::nordlys_scoring PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/nordlys_scoring.lib"
  )

list(APPEND _cmake_import_check_targets Nordlys::nordlys_scoring )
list(APPEND _cmake_import_check_files_for_Nordlys::nordlys_scoring "${_IMPORT_PREFIX}/lib/nordlys_scoring.lib" )

# Import target "Nordlys::nordlys_checkpoint" for configuration "Release"
set_property(TARGET Nordlys::nordlys_checkpoint APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(Nordlys::nordlys_checkpoint PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/nordlys_checkpoint.lib"
  )

list(APPEND _cmake_import_check_targets Nordlys::nordlys_checkpoint )
list(APPEND _cmake_import_check_files_for_Nordlys::nordlys_checkpoint "${_IMPORT_PREFIX}/lib/nordlys_checkpoint.lib" )

# Import target "Nordlys::nordlys_clustering" for configuration "Release"
set_property(TARGET Nordlys::nordlys_clustering APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(Nordlys::nordlys_clustering PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/nordlys_clustering.lib"
  )

list(APPEND _cmake_import_check_targets Nordlys::nordlys_clustering )
list(APPEND _cmake_import_check_files_for_Nordlys::nordlys_clustering "${_IMPORT_PREFIX}/lib/nordlys_clustering.lib" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
