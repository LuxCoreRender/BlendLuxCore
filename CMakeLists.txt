# To build extension:
# Get out of the tree, for instance in ..
# cmake -B blc-build -S BlendLuxCore && cmake --build blc-build

cmake_minimum_required(VERSION 3.25)

set(CMAKE_DISABLE_SOURCE_CHANGES ON)
set(CMAKE_DISABLE_IN_SOURCE_BUILD ON)
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE "Release")
endif()

project(BlendLuxCore LANGUAGES NONE)
if("${PROJECT_SOURCE_DIR}" STREQUAL "${PROJECT_BINARY_DIR}")
   message(SEND_ERROR "In-source builds are not allowed.")
endif()

function(validate_blender_version result blender)
  execute_process(
    COMMAND ${blender} --version
    OUTPUT_VARIABLE blender_output
  )
  if (blender_output MATCHES "Blender ([0-9]+\.[0-9]+\.[0-9]+).*")
    set(version ${CMAKE_MATCH_1})
    message(STATUS "Found Blender - version ${version}")
    if (${version} VERSION_LESS "4.2.0")
      message(FATAL_ERROR "ERROR: Blender version is not suitable - expected 4.2.0 or higher")
      set(${result} FALSE PARENT_SCOPE)
    else()
      message(STATUS "Blender version OK")
      set(${result} TRUE PARENT_SCOPE)
    endif()
  else()
    message(FATAL_ERROR "Blender version: Not found")
    set(${result} FALSE PARENT_SCOPE)
  endif()
endfunction()


# Get BlendLuxCore version
find_package(Python 3.11 REQUIRED COMPONENTS Interpreter)
if (CMAKE_BUILD_TYPE STREQUAL "Latest")
  set(BLC_VERSION "Latest")
else()
  execute_process(
    COMMAND python
      ${CMAKE_CURRENT_SOURCE_DIR}/cmake/blendluxcore_version.py
      ${CMAKE_CURRENT_SOURCE_DIR}/blender_manifest.toml
    OUTPUT_VARIABLE BLC_VERSION
  )
endif()

find_program(BLENDER blender NAMES blender.exe VALIDATOR validate_blender_version NO_CACHE REQUIRED)

# Add BlendLuxCore target
add_custom_target(
  extension ALL ${BLENDER}
    --command extension build
    --source-dir ${CMAKE_CURRENT_SOURCE_DIR}
    --output-filepath ${CMAKE_CURRENT_BINARY_DIR}/BlendLuxCore-${BLC_VERSION}.zip
  VERBATIM
)
