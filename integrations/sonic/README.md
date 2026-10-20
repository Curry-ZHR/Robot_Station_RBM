# XRoboToolkit lifecycle integration

`xrobotoolkit_runtime.py` is the reviewed project-local launcher used by SONIC's PC Service and PICO managers. This copy is shipped with Robot Station so service-stop functionality can be reproduced from the repository.

After installing the compatible `sonic_deploy` checkout and XR runtime, run:

```sh
bash scripts/install_xrobotoolkit_lifecycle.sh /path/to/sonic_deploy
```

The installer preserves the original source in SONIC's `.local-backups`, accepts the known baseline or an identical already-installed helper, and refuses to overwrite unrelated changes. Run the installed helper through `sonic_deploy/run_xrobotoolkit.sh`, rather than from this integration folder.

The extension adds `stop`, which sends SIGTERM through stable Linux pidfds to the exact project-owned PC Service and Unity executables, after checking visible controller/teleop/recording users. It verifies exit, does not force-kill an unresponsive process, and refuses another installation's processes. A persistent `outputs/xrobotoolkit/service.stopped` marker blocks implicit restart; explicit `service` or `3d` clears it. The web start button starts the PC Service only; use the existing `3d` launcher to reopen Unity.

Robot Station additionally checks active tasks, controller feedback, container ownership/processes, authorization, CSRF and revision/idempotency before service stops. This operation is infrastructure management, not a robot emergency stop.
