# Operator Console Layout

This document records the first-stage layout direction. It does not define ROS,
HTTP, or WebSocket interfaces.

## Overall Structure

- Left fixed navigation:
  - Control Center
  - Self Check
  - Homing
  - Manual Control
  - Data Collection
  - Inference
  - Sensors
  - Logs
  - Settings
- Top fixed status bar:
  - ROS status
  - CAN status
  - Emergency stop status
  - Robot enable status
  - Network status
  - Current task
  - Alert count
  - System time
- Main content:
  - Dense workbench layout.
  - Operator-readable task progress.
  - Hardware health summary.
- Right collapsible drawer:
  - Live logs
  - Alerts
  - Current task steps

## Home Page

- Row 1:
  - Whole-machine status strip.
  - Emergency stop and stop-task actions.
- Row 2:
  - Current task flow panel.
  - Alerts and recovery suggestions.
- Row 3:
  - Hardware health matrix:
    - Arm
    - Chassis
    - Cameras
    - LiDAR
    - Storage
    - Compute
- Row 4:
  - Quick actions:
    - Run self check
    - Home robot
    - Start data collection
    - Start inference
    - Open manual control

## Interaction Rules

- High-risk actions require confirmation:
  - Enable robot
  - Home robot
  - Start inference
  - Move chassis
  - Move arm
- Stop actions must always be visible.
- Mutually exclusive tasks must be disabled while another task owns the robot.
- Error messages must explain:
  - What happened.
  - What the operator should do next.
- Manual control starts collapsed and requires explicit entry confirmation.
- Motion control uses low-speed limits and always-visible stop actions.

## First Prototype Scope

The first UI prototype should prioritize:

- Control Center.
- Self Check.
- Homing.
- Data Collection.
- Inference.
- Status summary.
- Alerts and logs.

Full teleoperation is intentionally out of scope for the first version.

