#=============================================================================
# Copyright (c) 2026, NVIDIA CORPORATION.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#=============================================================================

#[=======================================================================[

Provide Python targets for cuPyNumeric.

Imported Targets:
  - cupynumeric::cupynumeric_python



Result Variables
^^^^^^^^^^^^^^^^

This module will set the following variables::

  CUPYNUMERIC_PYTHON_FOUND
  CUPYNUMERIC_PYTHON_VERSION
  CUPYNUMERIC_PYTHON_VERSION_MAJOR
  CUPYNUMERIC_PYTHON_VERSION_MINOR

#]=======================================================================]


####### Expanded from @PACKAGE_INIT@ by configure_package_config_file() #######
####### Any changes to this file will be overwritten by the next CMake run ####
####### The input file was config.cmake.in                            ########

get_filename_component(PACKAGE_PREFIX_DIR "${CMAKE_CURRENT_LIST_DIR}/../../../" ABSOLUTE)

macro(set_and_check _var _file)
  set(${_var} "${_file}")
  if(NOT EXISTS "${_file}")
    message(FATAL_ERROR "File or directory ${_file} referenced by variable ${_var} does not exist !")
  endif()
endmacro()

macro(check_required_components _NAME)
  foreach(comp ${${_NAME}_FIND_COMPONENTS})
    if(NOT ${_NAME}_${comp}_FOUND)
      if(${_NAME}_FIND_REQUIRED_${comp})
        set(${_NAME}_FOUND FALSE)
      endif()
    endif()
  endforeach()
endmacro()

####################################################################################

cmake_minimum_required(VERSION 3.30.4)

set(rapids_global_languages )
foreach(lang IN LISTS rapids_global_languages)
  include("${CMAKE_CURRENT_LIST_DIR}/cupynumeric_python-${lang}-language.cmake")
endforeach()
unset(rapids_global_languages)

include("${CMAKE_CURRENT_LIST_DIR}/cupynumeric_python-dependencies.cmake" OPTIONAL)
include("${CMAKE_CURRENT_LIST_DIR}/cupynumeric_python-targets.cmake" OPTIONAL)

if()
  set(cupynumeric_python_comp_names )
  # find dependencies before creating targets that use them
  # this way if a dependency can't be found we fail
  foreach(comp IN LISTS cupynumeric_python_FIND_COMPONENTS)
    if(${comp} IN_LIST cupynumeric_python_comp_names)
      file(GLOB cupynumeric_python_component_dep_files LIST_DIRECTORIES FALSE
           "${CMAKE_CURRENT_LIST_DIR}/cupynumeric_python-${comp}*-dependencies.cmake")
      foreach(f IN LISTS  cupynumeric_python_component_dep_files)
        include("${f}")
      endforeach()
    endif()
  endforeach()

  foreach(comp IN LISTS cupynumeric_python_FIND_COMPONENTS)
    if(${comp} IN_LIST cupynumeric_python_comp_names)
      file(GLOB cupynumeric_python_component_target_files LIST_DIRECTORIES FALSE
           "${CMAKE_CURRENT_LIST_DIR}/cupynumeric_python-${comp}*-targets.cmake")
      foreach(f IN LISTS  cupynumeric_python_component_target_files)
        include("${f}")
      endforeach()
      set(cupynumeric_python_${comp}_FOUND TRUE)
    endif()
  endforeach()
endif()

include("${CMAKE_CURRENT_LIST_DIR}/cupynumeric_python-config-version.cmake" OPTIONAL)

# Set our version variables
set(CUPYNUMERIC_PYTHON_VERSION_MAJOR 26)
set(CUPYNUMERIC_PYTHON_VERSION_MINOR 01)
set(CUPYNUMERIC_PYTHON_VERSION_PATCH 00)
set(CUPYNUMERIC_PYTHON_VERSION 26.01.00)


set(rapids_global_targets cupynumeric_python)
set(rapids_namespaced_global_targets cupynumeric_python)
if((NOT "cupynumeric::" STREQUAL "") AND rapids_namespaced_global_targets)
  list(TRANSFORM rapids_namespaced_global_targets PREPEND "cupynumeric::")
endif()

foreach(target IN LISTS rapids_namespaced_global_targets)
  if(TARGET ${target})
    get_target_property(_is_imported ${target} IMPORTED)
    get_target_property(_already_global ${target} IMPORTED_GLOBAL)
    if(_is_imported AND NOT _already_global)
      set_target_properties(${target} PROPERTIES IMPORTED_GLOBAL TRUE)
    endif()
  endif()
endforeach()

# For backwards compat
if("rapids_config_install" STREQUAL "rapids_config_build")
  foreach(target IN LISTS rapids_global_targets)
    if(TARGET ${target})
      get_target_property(_is_imported ${target} IMPORTED)
      get_target_property(_already_global ${target} IMPORTED_GLOBAL)
      if(_is_imported AND NOT _already_global)
        set_target_properties(${target} PROPERTIES IMPORTED_GLOBAL TRUE)
      endif()
      if(NOT TARGET cupynumeric::${target})
        add_library(cupynumeric::${target} ALIAS ${target})
      endif()
    endif()
  endforeach()
endif()

unset(rapids_comp_names)
unset(rapids_comp_unique_ids)
unset(rapids_global_targets)
unset(rapids_namespaced_global_targets)

check_required_components(cupynumeric_python)

set(${CMAKE_FIND_PACKAGE_NAME}_CONFIG "${CMAKE_CURRENT_LIST_FILE}")

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(${CMAKE_FIND_PACKAGE_NAME} CONFIG_MODE)


