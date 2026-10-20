#!/usr/bin/env python3
"""Local obstacle scan only: no pose estimation, accumulation, or map."""
import argparse
import asyncio
import json
import math
import queue
import threading
import time

from websockets.asyncio.client import connect
from websockets.exceptions import WebSocketException


def receive(url, inbox, stop):
    def update(item):
        try:
            inbox.put_nowait(item)
        except queue.Full:
            inbox.get_nowait()
            inbox.put_nowait(item)

    async def run():
        while not stop.is_set():
            try:
                update(('status', 'Connecting…'))
                async with connect(url, open_timeout=2, close_timeout=0.5,
                                   max_queue=1) as socket:
                    update(('status', 'Connected; waiting for scan'))
                    while not stop.is_set():
                        try:
                            raw = await asyncio.wait_for(socket.recv(), 0.5)
                        except asyncio.TimeoutError:
                            continue
                        message = json.loads(raw)
                        if message.get('type') != 'lidar_scan' or message.get('schema_version') != 1:
                            continue
                        update(('scan', message))
            except (OSError, ValueError, asyncio.TimeoutError,
                    WebSocketException) as exc:
                update(('status', f'Disconnected ({type(exc).__name__}); retrying…'))
                await asyncio.sleep(1)
    asyncio.run(run())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='ws://127.0.0.1:8765')
    args = parser.parse_args()
    # All GUI operations stay on the main thread.
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
    inbox, stop = queue.Queue(maxsize=2), threading.Event()
    worker = threading.Thread(target=receive, args=(args.url, inbox, stop), daemon=True)
    worker.start()
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
    fig.canvas.manager.set_window_title('Local obstacle scan — not a persistent map')
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(1)
    ax.set_ylim(0, 10)
    ax.set_title('Local obstacle scan — not a persistent map\nConnecting…', pad=25)
    points, = ax.plot([], [], '.', markersize=3)
    last_seen = None
    last_message = None

    def animate(_):
        nonlocal last_seen, last_message
        while True:
            try:
                kind, item = inbox.get_nowait()
            except queue.Empty:
                break
            if kind == 'status':
                points.set_data([], [])
                last_seen = None
                ax.set_title('Local obstacle scan — not a persistent map\n' + item, pad=25)
            else:
                angles, ranges = [], []
                for i, value in enumerate(item['ranges']):
                    if value is not None and math.isfinite(value):
                        angles.append(item['angle_min'] + i * item['angle_increment'])
                        ranges.append(value)
                points.set_data(angles, ranges)
                ax.set_ylim(0, item['range_max'])
                last_seen, last_message = time.monotonic(), item
        if last_seen is not None:
            stale = time.monotonic() - last_seen > 2
            m = last_message
            ax.set_title('Local obstacle scan — not a persistent map\n'
                         f'{"No new scan (paused/slow simulation?)" if stale else "Connected"}'
                         f' | scan {m["sequence"]} | sim {m["timestamp"]:.2f} s', pad=25)
        return points,

    animation = FuncAnimation(fig, animate, interval=50, cache_frame_data=False)
    fig.canvas.mpl_connect('close_event', lambda event: stop.set())
    try:
        plt.show()
    finally:
        stop.set()
        worker.join(timeout=2)


if __name__ == '__main__':
    main()
