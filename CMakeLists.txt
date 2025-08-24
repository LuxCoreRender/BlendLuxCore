# To build extension:
# cmake . && cmake --build .

cmake_minimum_required(VERSION 3.25)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE "Release")
endif()

project(BlendLuxCore LANGUAGES NONE)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR}/out)

# Create output directory (otherwise Blender complains)
file(MAKE_DIRECTORY ${CMAKE_RUNTIME_OUTPUT_DIRECTORY})


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
# https://docs.blender.org/manual/en/latest/advanced/command_line/extension_arguments.html
add_custom_target(
  extension ALL ${BLENDER}
    --command extension build
    --source-dir ${CMAKE_CURRENT_SOURCE_DIR}
    --output-filepath ${CMAKE_RUNTIME_OUTPUT_DIRECTORY}/BlendLuxCore-${BLC_VERSION}.zip
  VERBATIM
)

# Add install
# cmake --install .
install(CODE "
  execute_process(
    COMMAND ${BLENDER} --command extension install-file -r user_default ${CMAKE_RUNTIME_OUTPUT_DIRECTORY}/BlendLuxCore-${BLC_VERSION}.zip
    OUTPUT_VARIABLE INSTALL_OUTPUT
    ERROR_VARIABLE INSTALL_OUTPUT
  )
  message(STATUS ${INSTALL_OUTPUT})

")
