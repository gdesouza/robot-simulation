#!/usr/bin/env bash
# Linux X11/XWayland GUI, or headless simulation. Run from any directory.
set -euo pipefail
project_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
mode=${1:-gui}
if [[ "$mode" != gui && "$mode" != headless ]]; then
  echo "Usage: $0 [gui|headless] [Webots arguments...]" >&2
  exit 2
fi
if (( $# )); then shift; fi
command -v docker >/dev/null || { echo 'Install Docker Engine first.' >&2; exit 1; }
if ! docker info >/dev/null 2>&1; then
  echo 'Cannot access the Docker daemon. Start Docker and configure your user for daemon access.' >&2
  exit 1
fi
image=${WEBOTS_CONTAINER_IMAGE:-indoor-webots:r2025a}
port=${LIDAR_PORT:-8765}
if [[ ! "$port" =~ ^[0-9]+$ ]] || (( 10#$port < 1 || 10#$port > 65535 )); then
  echo 'LIDAR_PORT must be between 1 and 65535.' >&2; exit 2
fi
args=(--rm --init --shm-size=512m --user "$(id -u):$(id -g)"
      --env USER="$(id -un)" --env HOME=/tmp/webots-home
      --publish "127.0.0.1:${port}:8765"
      --mount "type=bind,source=${project_dir},target=/workspace")
for variable in CAMERA_HZ LIDAR_HZ ROBOT_MAX_WHEEL_SPEED; do
  if [[ -v "$variable" ]]; then args+=(--env "$variable"); fi
done
cookie_dir=''
cleanup() { if [[ -n "$cookie_dir" ]]; then rm -rf -- "$cookie_dir"; fi; }
trap cleanup EXIT
if [[ "$mode" == gui ]]; then
  : "${DISPLAY:?DISPLAY is required for GUI; use headless without a desktop}"
  command -v xauth >/dev/null || { echo 'Install xauth on the host.' >&2; exit 1; }
  [[ -d /tmp/.X11-unix ]] || { echo 'No local X11/XWayland socket directory found.' >&2; exit 1; }
  cookie_dir=$(mktemp -d)
  touch "$cookie_dir/Xauthority"
  chmod 600 "$cookie_dir/Xauthority"
  # FamilyWild lets the same display cookie work with the container hostname.
  xauth nlist "$DISPLAY" | sed 's/^..../ffff/' | xauth -f "$cookie_dir/Xauthority" nmerge -
  if [[ ! -s "$cookie_dir/Xauthority" ]]; then
    echo 'No Xauthority cookie for DISPLAY. Set XAUTHORITY to your desktop session authority file.' >&2
    exit 1
  fi
  args+=(--env DISPLAY --env XAUTHORITY=/tmp/container.Xauthority
         --mount 'type=bind,source=/tmp/.X11-unix,target=/tmp/.X11-unix,readonly'
         --mount "type=bind,source=${cookie_dir}/Xauthority,target=/tmp/container.Xauthority,readonly")
fi
case "${WEBOTS_GPU:-software}" in
  software) args+=(--env LIBGL_ALWAYS_SOFTWARE=1) ;;
  dri)
    [[ -d /dev/dri ]] || { echo '/dev/dri is unavailable.' >&2; exit 1; }
    args+=(--device /dev/dri)
    for node in /dev/dri/*; do
      [[ -c "$node" ]] && args+=(--group-add "$(stat -c %g "$node")")
    done
    ;;
  nvidia) args+=(--gpus all --env NVIDIA_DRIVER_CAPABILITIES=graphics,compute,utility) ;;
  *) echo 'WEBOTS_GPU must be software, dri, or nvidia.' >&2; exit 2 ;;
esac
# Keep this shell alive so the temporary display cookie is removed after exit.
docker run "${args[@]}" "$image" "$mode" "$@"
