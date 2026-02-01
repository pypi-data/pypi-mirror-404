include(CMakeFindDependencyMacro)

# This macro handles relocatability and package prefix calculation.

####### Expanded from @PACKAGE_INIT@ by configure_package_config_file() #######
####### Any changes to this file will be overwritten by the next CMake run ####
####### The input file was ddvisitor-config.cmake.in                            ########

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

# 0. Dependencies
if (NOT TARGET tp::tpack)
	find_dependency(tpack REQUIRED)
else ()
	message(STATUS "tpack target (tp::tpack) already defined in build tree. Skipping find_dependency.")
endif ()

# 1. Include the Targets File
if (NOT TARGET ddv::ddvisitor)
	include("${CMAKE_CURRENT_LIST_DIR}/ddvisitor-targets.cmake")
endif ()

# 2. Check for required components
check_required_components(ddvisitor)
