# Indoor mobile robot — Webots + Python

Standalone, ROS-free differential-drive robot in an 8 × 6 m indoor room. Two powered wheels and a passive spherical caster support a 3 kg chassis. Walls, floor, partitions, and six furniture-like solid blocks have collision geometry. Two 0.8 m doorways join the room sections. The robot starts at (-3, -2), facing +X, clear of furniture. No external PROTO downloads are needed.

## Run Webots in Docker (Linux desktop)

This is an alternative to installing Webots on the host. The image extends **`cyberbotics/webots:R2025a-ubuntu22.04`**, matching the world version, and installs only the Python controller dependency in `/opt/robot-venv`. The host runs the Matplotlib receiver. The launcher supports Linux X11 and Wayland desktops with XWayland (`DISPLAY` and `/tmp/.X11-unix` available). It does not configure GUI forwarding for macOS, Windows, or SSH displays.

Prerequisites: Docker Engine with daemon access for your user, host `xauth`, and Python 3.10+ with a GUI backend for the receiver. On Ubuntu, host packages are `xauth python3-venv python3-tk`. No host Webots installation or Webots Python preference change is required for this path.

Build once:

```bash
cd /home/gustavo/Workspace/indoor-webots
docker build -t indoor-webots:r2025a .
```

Launch the GUI and world:

```bash
./docker/run.sh
```

The world starts in real-time mode. Click **the container's Webots 3D scene** and hold WASD/arrows; Space or key release commands a stop. Use the camera overlay/Robot Window and LiDAR optional rendering described below. Closing Webots removes the container. The launcher runs as your host UID/GID and mounts this project at `/workspace`, so world edits saved in Webots persist on the host without root-owned files. Container preferences are temporary; controller Python is configured automatically. Do not select the host `.venv` in the container.

In a second host terminal:

```bash
cd /home/gustavo/Workspace/indoor-webots
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python clients/lidar_receiver.py
```

Validate the live stream from another terminal while Webots runs:

```bash
.venv/bin/python clients/check_stream.py
```

The controller binds `0.0.0.0:8765` **inside** the container so Docker port forwarding can reach it. Docker publishes it only at **host `127.0.0.1:8765`**. The noncontainer controller still defaults to loopback. Change the host port with:

```bash
LIDAR_PORT=8877 ./docker/run.sh
# On the host:
.venv/bin/python clients/lidar_receiver.py --url ws://127.0.0.1:8877
```

`CAMERA_HZ`, `LIDAR_HZ`, and `ROBOT_MAX_WHEEL_SPEED` are also forwarded when set. The container-side port stays 8765. Only one container can publish a given host port.

The default renderer is software OpenGL, avoiding host GPU setup. It can be slow at 640 × 480; simulated sensor rates still follow simulation time. To use an Intel/AMD GPU via `/dev/dri`, or an NVIDIA GPU with the NVIDIA Container Toolkit already installed:

```bash
WEBOTS_GPU=dri ./docker/run.sh
# Or:
WEBOTS_GPU=nvidia ./docker/run.sh
```

X11 access uses a temporary, read-only Xauthority cookie and socket mount; no `xhost +` command or privileged container is needed. On Wayland, `XAUTHORITY` must identify the session's XWayland authority file if `xauth` cannot find the cookie automatically. The temporary cookie file is removed on normal launcher exit. The forwarded GUI uses your desktop session; launch only an image you trust.

For a display-free run:

```bash
./docker/run.sh headless
```

This uses the image's Xvfb and keeps camera/LiDAR rendering active. It streams stationary scans, but **there is no visible camera feed or interactive keyboard driving** in headless mode. Use GUI mode to validate the manual driving requirements. Ctrl+C stops a headless run.

Additional Webots arguments may follow the mode, e.g. `./docker/run.sh gui --batch`. Set `WEBOTS_CONTAINER_IMAGE` to select a different locally built project image. To change the upstream image at build time, use `docker build --build-arg WEBOTS_IMAGE=cyberbotics/webots:R2025a-ubuntu22.04 -t indoor-webots:r2025a .`; keep the R2025a version unless you also review world and preference compatibility.

Container troubleshooting:

- **Docker socket permission denied**: confirm `docker info` works in your host terminal. Start the daemon or configure Docker/rootless Docker access using your system's setup. This launcher does not change group memberships or socket permissions.
- **Cannot open display / no authority cookie**: run from a terminal in the graphical login session, check `DISPLAY` and `XAUTHORITY`, and install host `xauth`. The launcher expects local X11/XWayland rather than an SSH-forwarded display.
- **Scene says No Rendering**: the container startup preferences now explicitly set `rendering=true`. Rebuild with `docker build -t indoor-webots:r2025a .` and restart the GUI launcher after updating `docker/entrypoint.sh`; that script is copied into the image, so a bind-mounted project update alone does not replace it.
- **OpenGL initialization fails**: start with the software default. For GPU mode, check host drivers and `/dev/dri` permissions or NVIDIA Container Toolkit configuration. Do not use `--no-rendering`: it prevents the camera/LiDAR validation this project requires.
- **Connection refused on the receiver**: check the controller console, host port conflicts, and Docker port publishing. The receiver runs on the host, connecting to `127.0.0.1`, rather than to a container IP.
- **World edits disappear**: launch through `docker/run.sh`, which bind-mounts the project. A direct run of the image without that mount uses an ephemeral project copy.
- **Restricted environment**: Docker CLI is present on the build machine, but daemon access was denied. Shell syntax checks and a mocked launcher invocation passed; an actual image build, GUI/GPU run, and container stream test remain unverified.

References: [Cyberbotics Docker image tags](https://hub.docker.com/r/cyberbotics/webots/tags), [official GUI and headless Docker instructions](https://cyberbotics.com/doc/guide/installation-procedure), and [upstream Dockerfile](https://github.com/cyberbotics/webots-docker/blob/master/Dockerfile).

## Native installation and launch

Prerequisites: **Webots R2025a** (the file/API target, not simulator-tested here), Python **3.10+**, and a desktop with OpenGL support. Get Webots from https://cyberbotics.com/. The receiver needs a working Matplotlib GUI backend (for example Tk; on Ubuntu install `python3-tk` and `python3-venv`). No ROS installation is needed.

On this machine, run:

```bash
cd /home/gustavo/Workspace/indoor-webots
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

In Webots, open **Tools → Preferences → General → Python command** and set it to the absolute path:

```text
/home/gustavo/Workspace/indoor-webots/.venv/bin/python
```

On macOS the preferences dialog is in the application menu; on Windows use the venv's `Scripts/python.exe`. If you move the project, update this path.

Open **File → Open World**, select:

```text
/home/gustavo/Workspace/indoor-webots/worlds/indoor.wbt
```

Alternatively, from the project directory, with `webots` on PATH:

```bash
webots worlds/indoor.wbt
```

Press **Run / real-time** in Webots. The `indoor_driver` Python controller starts automatically. Its console prints sensor periods and `LiDAR WebSocket: ws://127.0.0.1:8765`.

Select IndoorBot in the 3D view. The enabled `front camera` image can be shown as a device overlay using the robot's device/overlay menu in the 3D view; if hidden, open the robot's **Robot Window** (generic robot window) and expand the camera device. Enable **View → Optional Rendering → Show Lidar Point Cloud** for the live 3D scan/rays. The controller calls `enablePointCloud()`; the optional rendering toggle controls visibility. Camera and LiDAR stay inside Webots; only LiDAR is streamed externally.

In a **second terminal**, start the receiver:

```bash
cd /home/gustavo/Workspace/indoor-webots
.venv/bin/python clients/lidar_receiver.py
```

The polar plot is labeled **Local obstacle scan — not a persistent map**. Forward is at the top, left is on the left. It shows only the latest scan, discards old plot updates, clears on disconnect, and reconnects once per second after a simulator restart. Sequence numbers restart at 1 and simulation time restarts after a world reset. A paused simulation produces no new scans; the plot labels scans stale after two wall-clock seconds. Close the plot to stop the receiver.

## Drive

**Click the Webots 3D scene to give it keyboard focus.** The terminal, receiver plot, scene tree, and text editor do not forward drive keys. Keep the simulation running.

| Hold key | Action |
|---|---|
| W / Up | Forward |
| S / Down | Reverse |
| A / Left | Turn left in place |
| D / Right | Turn right in place |
| Space | Zero wheel-speed command, overriding all movement keys |
| Release movement keys | Zero wheel-speed command on the next control step |

Forward/reverse can combine with turning; opposite keys cancel. Each 10 ms simulated step reads the current pressed-key set, never a latched last command. Space and release command a stop immediately at that control cadence; physical braking takes finite time. Release keys before switching application focus. Pausing freezes physics; use Space after resuming if needed. Real-time mode is recommended for manual driving.

## Configuration and geometry

Change the `IndoorBot { ... }` fields in `worlds/indoor.wbt` (or the defaults in `protos/IndoorBot.proto`). Reset/reload the world after editing geometry. The custom model keeps wheel geometry tunable without duplicating a bundled robot's hidden physical constants.

| Setting | Default |
|---|---|
| `wheelRadius`, `wheelWidth`, `axleTrack` | 0.065 m, 0.035 m, 0.30 m between wheel centers |
| `maxWheelSpeed` | 8 rad/s; straight-line ceiling 0.52 m/s |
| Camera `cameraWidth`, `cameraHeight` | 640 × 480 RGB scene, Webots native BGRA buffer |
| Camera horizontal FOV | 60 degrees; edit Camera node in PROTO |
| Camera period | 70 ms = **14.286 frames per simulated second** |
| `lidarSamples`, `lidarMaxRange` | 360, 10 m |
| LiDAR minimum range / near clipping | 0.05 m / 0.02 m |
| LiDAR period | 100 ms = **10 scans per simulated second** |
| LiDAR | fixed cylindrical 360° FOV, 1 horizontal layer, zero tilt/noise |
| LiDAR vertical FOV | 0.04 rad; single layer lies at zero elevation |
| Camera / LiDAR origin | (0.165, 0, radius + 0.10) / (0, 0, radius + 0.20) m |
| World basic time step | 10 ms |

Periods are rounded to the nearest positive multiple of the world's basic time step. The 0.04-rad LiDAR vertical FOV satisfies Webots' raster constraint at 360 samples, while the single sampled layer is horizontal. Keep `verticalFieldOfView * lidarSamples / (2*pi) > 1` when changing resolution. Geometry should keep positive wheel dimensions, sufficient chassis clearance, and wheel track wider than the body; large changes need physics verification. Furniture is represented by solid blocks, not hollow desks, so the scan sees their full footprint.

Controller environment variables:

| Variable | Default | Meaning |
|---|---|---|
| `LIDAR_HOST` | `127.0.0.1` | IPv4 loopback bind address |
| `LIDAR_PORT` | `8765` | WebSocket port |
| `ROBOT_MAX_WHEEL_SPEED` | PROTO value | Positive speed cap, clamped to motor limits |
| `CAMERA_HZ` | `15` | Positive requested camera rate |
| `LIDAR_HZ` | `10` | Positive requested scan rate |

For example, fully quit Webots, then launch it from a terminal so the controller inherits the environment:

```bash
LIDAR_PORT=8877 webots worlds/indoor.wbt
# In another terminal:
.venv/bin/python clients/lidar_receiver.py --url ws://127.0.0.1:8877
```

## LiDAR stream v1

Endpoint: `ws://127.0.0.1:8765` (any URL path). Text JSON messages only. Example shortened for readability; a real default message has exactly 360 `ranges` entries:

```json
{
  "type": "lidar_scan",
  "schema_version": 1,
  "sequence": 1,
  "timestamp": 0.1,
  "frame_id": "lidar",
  "angle_min": -3.1328660073298216,
  "angle_max": 3.1328660073298216,
  "angle_increment": 0.017453292519943295,
  "range_min": 0.05,
  "range_max": 10.0,
  "ranges": [2.1, null, 3.4]
}
```

`timestamp` is Webots `Robot.getTime()` in seconds at acquisition completion, not Unix time. `sequence` increases for every acquired scan, including scans dropped before delivery. Within a controller run, delivered scan sequences and timestamps increase; a restart/reset establishes a new run. Gaps are intentional under load.

Frame `lidar` is centered on the sensor: **+X forward, +Y left, +Z up**, aligned with the robot. Angles are radians about +Z, positive counterclockwise from forward. Sample `i` is at `angle_min + i * angle_increment`. Samples are pixel centers from **-179.5° to +179.5°**, increasing by 1°; the rear seam is not duplicated. This reverses Webots' native left-to-right order. For projection, `x = r*cos(angle)`, `y = r*sin(angle)`. `angle_min` and `angle_max` are the actual first and last ray centers, not the full FOV edges. Null denotes nonfinite, too-near, or out-of-range returns. JSON serialization forbids NaN/Infinity.

Acquisition follows **simulation time**. Delivery follows **wall-clock network scheduling** on a worker thread: at real-time speed expect about 10 messages/s; faster simulation can yield more or drop scans, and slower simulation yields fewer. Pausing produces no new scans (a pending scan may still arrive). One message is formed per new scan; delivery is best effort, not lossless logging. No backlog is replayed on connection.

The simulation only performs a nonblocking enqueue to a queue of capacity 2. The worker drains it every 5 ms wall time, preferring the newest scan, and each client has a capacity-1 queue. Slow sends time out after 0.5 s and disconnect with code 1013, allowing reconnection. WebSocket write buffering is bounded by flow control; other clients and manual control do not wait for it. No connected client is required. A port-bind failure logs an error but leaves driving and sensing active. Only the simulation thread calls Webots APIs. The endpoint is intended for local clients and has no authentication.

## Code layout and future control

- `protos/IndoorBot.proto`: parameterized wheels, chassis, passive ball caster, camera, LiDAR.
- `worlds/indoor.wbt`: self-contained collision world and robot start.
- `controllers/indoor_driver/indoor_driver.py`: simulation loop and motor commands.
- `keyboard_control.py`: manual policy; future autonomous policy can return the same left/right wheel command pair here.
- `sensors.py`: sampling cadence, simulation timestamps, sensor frame conversion, JSON schema.
- `streaming.py`: isolated network thread and bounded queues.
- `clients/lidar_receiver.py`: reconnecting plotting client; all GUI operations on its main thread.
- `tests/test_project.py`: controller/schema checks and loopback integration test.

There is no SLAM, persistent map, autonomous navigation, ROS, or external camera stream.

## Validation and simulator acceptance checklist

Run local checks with:

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q controllers clients tests
```

On the build machine, **Webots was not installed**. Four tests passed: manual key/release/Space command logic, strict JSON and 360-sample angle/range conversion, simulated acquisition cadence with increasing sequence/timestamps using fake devices, and bounded queues / slow-client timeout using a fake socket. Python compilation passed. Cached `websockets 17.2` was installed in the project venv. The real loopback integration test was attempted but the sandbox forbids binding localhost sockets; consequently actual transport/reconnection is **not verified** here. Matplotlib installation was blocked by unavailable package downloads, so GUI execution is also unverified. On an unrestricted desktop, the loopback test exercises real connects, multiple scans, disconnect/reconnect, bounded queues, no-client publication, and clean server shutdown. It must pass before considering transport validated.

Complete these checks in Webots before relying on physical behavior:

For a live schema check while the world runs, execute `.venv/bin/python clients/check_stream.py` (20 scans by default). It fails on invalid JSON, sample count, ranges, angles, or non-increasing sequence/time. Run again after restarting Webots; use the plot to verify reconnects across a restart.

1. Open the world with no parser/physics errors; run real-time. Confirm camera overlay/window updates and LiDAR point cloud/rays are visible.
2. Hold each WASD and arrow key; verify direction, release-to-stop, Space priority, combined driving, and restart from a stop. Confirm no motion with no keys pressed.
3. Drive into a wall and furniture; verify physical contact blocks passage. Drive through both doorways and check caster stability.
4. Start receiver; verify exactly 360 samples, valid JSON, increasing sequences/timestamps, front/left obstacle alignment, and changing distances while translating/turning. A wall straight ahead should appear near angle zero.
5. Close/reopen receiver while driving; verify uninterrupted control. Restart/reset Webots with receiver open and verify reconnection and fresh sequence/time.
6. Drive without any receiver. Test with a slow/nonreading client and confirm control responsiveness. Pause/resume and vary simulation speed to check the documented timing behavior.

## Troubleshooting

- **`No module named websockets`**: Webots must use the same project venv Python as the installation command; set Preferences, then reset the simulation. Do not install the unrelated PyPI `controller` package; Webots supplies its own module.
- **No motion**: run the simulation, click the 3D scene, select IndoorBot, and hold a movement key. Check the controller console for configuration errors.
- **Camera hidden / no scan points**: select the robot, show its camera device overlay or generic Robot Window, and enable LiDAR point-cloud optional rendering. Check that the controller is running. GPU drivers/OpenGL must support Webots camera rendering.
- **Receiver cannot connect**: inspect the controller console for bind failures, confirm host/port match, and stop any previous process using the port. Use `127.0.0.1` rather than `localhost` to avoid IPv6 mismatches. A paused simulator can still accept connections but sends no new scans.
- **Plot window missing**: install a GUI backend such as Tk and run from a graphical desktop. `MPLBACKEND=TkAgg .venv/bin/python clients/lidar_receiver.py` can select Tk explicitly.
- **Low simulation speed**: use real-time mode, reduce camera resolution/rate, or hide expensive optional rendering. Rendering and physics can slow simulation even though network calls are isolated.
- **World changes not applied**: reset/reload the world after editing PROTO fields. Do not edit sampling periods without respecting the basic time step.

Implementation references: [Webots keyboard API](https://cyberbotics.com/doc/reference/keyboard), [LiDAR API](https://cyberbotics.com/doc/reference/lidar), and [R2025a LiDAR point projection source](https://github.com/cyberbotics/webots/blob/R2025a/src/webots/nodes/WbLidar.cpp) for sample-center angles and FLU coordinates.
