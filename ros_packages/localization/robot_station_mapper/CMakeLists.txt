cmake_minimum_required(VERSION 3.14)
project(robot_station_mapper)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(ament_cmake REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(pcl_conversions REQUIRED)
find_package(PCL REQUIRED COMPONENTS common filters io registration)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_sensor_msgs REQUIRED)

add_executable(robot_station_mapper_cli src/mapper_cli.cpp)
target_include_directories(robot_station_mapper_cli PRIVATE ${PCL_INCLUDE_DIRS})
target_link_libraries(robot_station_mapper_cli ${PCL_LIBRARIES})
ament_target_dependencies(
  robot_station_mapper_cli
  geometry_msgs
  nav_msgs
  pcl_conversions
  rclcpp
  sensor_msgs
  tf2
  tf2_ros
  tf2_sensor_msgs
)

install(TARGETS robot_station_mapper_cli DESTINATION lib/${PROJECT_NAME})

ament_package()
