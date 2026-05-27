# Architecture Notes

## Direction

Robot Station follows a layered robot-system structure:

- `frontend` provides the operator console.
- `backend` owns local orchestration, permissions, state transitions, and API
  boundaries.
- `modules` owns task-level logic such as self check, homing, data collection,
  inference, monitoring, and safety.
- `ros` owns ROS launch files and ROS packages that belong to this project.
- `sdk` owns hardware SDK wrappers and vendor integration code.
- `config` owns robot profiles and environment-specific settings.

## Boundaries

### Frontend

The frontend should stay focused on operator workflows:

- Task control center.
- Self-check report.
- Homing progress.
- Low-speed constrained manual control.
- Data collection workflow.
- Inference workflow.
- Sensor and robot status pages.
- Logs, alerts, and task history.

It should not contain direct hardware control logic.

### Backend

The backend should become the only place that coordinates high-level task
ownership:

- Idle.
- Preparing.
- Running.
- Paused.
- Stopping.
- Failed.
- Completed.

Only one high-level task should own the robot at a time.

### Modules

Modules should be independent enough to run from the backend or from scripts when
needed. They should expose clear task inputs, task state, task result, and
operator-readable failure reasons.

### ROS

ROS code can be started independently or by Robot Station later. Existing ROS
code should not be moved into this folder until its ownership is clear.

### SDK

SDK wrappers should isolate vendor-specific details from task modules. For
example, Piper-specific control code can live under `sdk/piper`, while AgileX
base-specific code can live under `sdk/agilex`.

## Safety Model

Robot Station should eventually include:

- Global stop.
- Robot task ownership.
- Low-speed arm limit.
- Low-speed chassis limit.
- Manual-control timeout.
- Stale self-check detection.
- Operator-readable recovery suggestions.

