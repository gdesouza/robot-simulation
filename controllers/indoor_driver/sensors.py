"""Simulation-thread sensor access and strict wire format."""
import json
import math


def scan_message(raw, sequence, timestamp, fov, minimum, maximum):
    # Fixed cylindrical lidar uses pixel centers; reverse native left-to-right
    # order to increasing counterclockwise angles in the FLU sensor frame.
    n = len(raw)
    increment = fov / n
    return {
        'type': 'lidar_scan', 'schema_version': 1,
        'sequence': sequence, 'timestamp': timestamp, 'frame_id': 'lidar',
        'angle_min': -fov / 2 + increment / 2,
        'angle_max': fov / 2 - increment / 2,
        'angle_increment': increment,
        'range_min': minimum, 'range_max': maximum,
        'ranges': [float(v) if math.isfinite(v) and minimum <= v <= maximum
                   else None for v in reversed(raw)],
    }


def encode_scan(message):
    return json.dumps(message, allow_nan=False, separators=(',', ':'))


def period_ms(target_hz, step):
    if not math.isfinite(target_hz) or target_hz <= 0:
        raise ValueError("Sensor rate must be finite and positive")
    return max(step, round(1000 / target_hz / step) * step)


class Sensors:
    def __init__(self, robot, step, camera_hz=15, lidar_hz=10):
        self.camera = robot.getDevice('front camera')
        self.lidar = robot.getDevice('lidar')
        self.camera.enable(period_ms(camera_hz, step))
        self.period = period_ms(lidar_hz, step)
        self.lidar.enable(self.period)
        self.lidar.enablePointCloud()
        self.sequence = 0
        self.ticks = 0
        self.stride = self.period // step
        print(f'Camera: {self.camera.getWidth()}x{self.camera.getHeight()}, '
              f'{self.camera.getSamplingPeriod()} ms; LiDAR: '
              f'{self.lidar.getHorizontalResolution()} samples, {self.period} ms')

    def poll(self, timestamp):
        self.ticks += 1
        if self.ticks % self.stride:
            return None
        raw = self.lidar.getRangeImage()
        if len(raw) != self.lidar.getHorizontalResolution():
            raise ValueError('Expected a single-layer LiDAR')
        self.sequence += 1
        return scan_message(raw, self.sequence, timestamp,
                            self.lidar.getFov(), self.lidar.getMinRange(),
                            self.lidar.getMaxRange())
