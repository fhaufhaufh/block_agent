execute_process(COMMAND "/home/ytm/block_agent/build/block_building_agent/catkin_generated/python_distutils_install.sh" RESULT_VARIABLE res)

if(NOT res EQUAL 0)
  message(FATAL_ERROR "execute_process(/home/ytm/block_agent/build/block_building_agent/catkin_generated/python_distutils_install.sh) returned error code ")
endif()
