#!/usr/bin/env bash
exec ros2 launch robot_station_camera_bringup cameras.launch.py \
  front_serial:="CC136530352" \
  left_serial:="CC1365303LY" \
  right_serial:="CC136530160"
