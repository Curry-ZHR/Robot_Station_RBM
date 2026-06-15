cmake_minimum_required(VERSION 3.14)
project(robot_station_mapper)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

option(ROBOT_STATION_ENABLE_GPU_LOCALIZER "Build optional CUDA fast_gicp localizer" ON)

find_package(ament_cmake REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(pcl_conversions REQUIRED)
find_package(PCL REQUIRED COMPONENTS common filters io registration)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_sensor_msgs REQUIRED)
find_package(fast_gicp QUIET)

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

add_executable(robot_station_localizer_node src/localizer_node.cpp)
target_include_directories(robot_station_localizer_node PRIVATE ${PCL_INCLUDE_DIRS})
target_link_libraries(robot_station_localizer_node ${PCL_LIBRARIES})
ament_target_dependencies(
  robot_station_localizer_node
  geometry_msgs
  nav_msgs
  pcl_conversions
  rclcpp
  sensor_msgs
  std_msgs
  tf2
  tf2_ros
  tf2_sensor_msgs
)

install(TARGETS robot_station_localizer_node DESTINATION lib/${PROJECT_NAME})

if(ROBOT_STATION_ENABLE_GPU_LOCALIZER AND fast_gicp_FOUND)
  find_library(FAST_VGICP_CUDA_LIBRARY fast_vgicp_cuda)
  if(FAST_VGICP_CUDA_LIBRARY)
    add_executable(robot_station_gpu_localizer_node src/localizer_node.cpp)
    target_compile_definitions(
      robot_station_gpu_localizer_node
      PRIVATE
        ROBOT_STATION_USE_FAST_GICP_CUDA
        USE_VGICP_CUDA
    )
    target_include_directories(robot_station_gpu_localizer_node PRIVATE ${PCL_INCLUDE_DIRS})
    target_link_libraries(
      robot_station_gpu_localizer_node
      ${PCL_LIBRARIES}
      ${FAST_VGICP_CUDA_LIBRARY}
    )
    ament_target_dependencies(
      robot_station_gpu_localizer_node
      fast_gicp
      geometry_msgs
      nav_msgs
      pcl_conversions
      rclcpp
      sensor_msgs
      std_msgs
      tf2
      tf2_ros
      tf2_sensor_msgs
    )

    install(TARGETS robot_station_gpu_localizer_node DESTINATION lib/${PROJECT_NAME})
  else()
    message(STATUS "fast_gicp found without fast_vgicp_cuda; GPU localizer will not be built")
  endif()
else()
  message(STATUS "fast_gicp not found or GPU localizer disabled; GPU localizer will not be built")
endif()

ament_package()
