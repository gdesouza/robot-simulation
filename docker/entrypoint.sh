#!/usr/bin/env bash
set -euo pipefail
mkdir -p "$HOME/.config/Cyberbotics"
# This home is container-local, so host Webots preferences cannot select a host venv.
cat > "$HOME/.config/Cyberbotics/Webots-R2025a.conf" <<'CONF'
[%General]
pythonCommand=/opt/robot-venv/bin/python
rendering=true
checkWebotsUpdateOnStartup=false
telemetry=false
[Internal]
firstLaunch=false
[Sound]
mute=true
CONF
case "${1:-gui}" in
  gui)
    shift || true
    exec webots --stdout --stderr --mode=realtime /workspace/worlds/indoor.wbt "$@"
    ;;
  headless)
    shift
    exec xvfb-run -a -s '-screen 0 1280x1024x24' webots --stdout --stderr --batch \
      --mode=realtime /workspace/worlds/indoor.wbt "$@"
    ;;
  *) exec "$@" ;;
esac
