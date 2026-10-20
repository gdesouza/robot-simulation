"""Webots entry point. Only this thread touches Webots devices."""
import json
import os
from controller import Robot
from keyboard_control import read_keys, wheel_commands
from sensors import Sensors, encode_scan
from streaming import ScanServer


def main():
    robot = Robot()
    step = int(robot.getBasicTimeStep())
    config = json.loads(robot.getCustomData())
    motors = [robot.getDevice(name + ' wheel motor') for name in ('left', 'right')]
    for motor in motors:
        motor.setPosition(float('inf'))
        motor.setVelocity(0)
    keyboard = robot.getKeyboard()
    keyboard.enable(step)
    maximum = min(float(os.getenv('ROBOT_MAX_WHEEL_SPEED', config['max_wheel_speed'])),
                  *(motor.getMaxVelocity() for motor in motors))
    if maximum <= 0:
        raise ValueError('Maximum wheel speed must be positive')
    sensors = Sensors(robot, step,
                      float(os.getenv('CAMERA_HZ', '15')),
                      float(os.getenv('LIDAR_HZ', '10')))
    stream = ScanServer(os.getenv('LIDAR_HOST', '127.0.0.1'),
                        int(os.getenv('LIDAR_PORT', '8765')))
    stream.start()
    print('Click the Webots 3D view. Hold WASD/arrows; release or Space stops.')
    try:
        while robot.step(step) != -1:
            command = wheel_commands(read_keys(keyboard), keyboard, maximum)
            for motor, speed in zip(motors, command):
                motor.setVelocity(speed)
            scan = sensors.poll(robot.getTime())
            if scan is not None:
                stream.publish(encode_scan(scan))
    finally:
        for motor in motors:
            motor.setVelocity(0)
        stream.close()


if __name__ == '__main__':
    main()
