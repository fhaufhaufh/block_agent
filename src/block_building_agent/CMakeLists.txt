cmake_minimum_required(VERSION 3.0.2)
project(block_building_agent)

## Find catkin macros and libraries
find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
)

## ✅ 启用 Python setup（取消注释）
catkin_python_setup()

###################################
## catkin specific configuration ##
###################################
catkin_package(
  CATKIN_DEPENDS rospy std_msgs
)

###########
## Build ##
###########
include_directories(
  ${catkin_INCLUDE_DIRS}
)

#############
## Install ##
#############

## ✅ 安装 Python 脚本（取消注释并配置）
catkin_install_python(PROGRAMS
  scripts/planning_node.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

## ✅ 安装 launch 文件（取消注释）
install(DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
)

## ✅ 安装 Python 包（新增）
install(DIRECTORY src/block_building_agent/
  DESTINATION ${CATKIN_PACKAGE_PYTHON_DESTINATION}
  FILES_MATCHING PATTERN "*.py"
  PATTERN ".git" EXCLUDE
)

## ✅ 安装 config 文件（如果有）
install(DIRECTORY config/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/config
  OPTIONAL
)

#############
## Testing ##
#############
## ✅ 启用测试（取消注释）
catkin_add_nosetests(test)