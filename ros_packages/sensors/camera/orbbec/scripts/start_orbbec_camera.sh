#!/usr/bin/env bash
exec ros2 launch orbbec_camera multi_camera.launch.py \
  front_serial:="CC136530352" \
  left_serial:="CC1365303LY" \
  right_serial:="CC136530160"
