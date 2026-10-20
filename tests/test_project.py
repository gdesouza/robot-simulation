import asyncio
import json
import math
from pathlib import Path
import queue
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'controllers/indoor_driver'))
from keyboard_control import wheel_commands
from sensors import scan_message, encode_scan, period_ms


class Keys:
    UP, DOWN, LEFT, RIGHT = 315, 317, 314, 316


class ControlAndSchema(unittest.TestCase):
    def test_hold_release_and_stop_priority(self):
        self.assertEqual(wheel_commands({ord('W')}, Keys, 8), (8, 8))
        self.assertEqual(wheel_commands(set(), Keys, 8), (0, 0))
        self.assertEqual(wheel_commands({ord('W'), 32}, Keys, 8), (0, 0))
        self.assertEqual(wheel_commands({Keys.DOWN}, Keys, 8), (-8, -8))
        a, b = wheel_commands({Keys.LEFT}, Keys, 8)
        self.assertLess(a, 0)
        self.assertGreater(b, 0)
        for keys in ({ord('W'), ord('A')}, {ord('S'), ord('D')}):
            self.assertLessEqual(max(map(abs, wheel_commands(keys, Keys, 8))), 8)

    def test_scan_sanitization_size_and_angles(self):
        raw = [float('nan'), float('inf'), -1, 11, 0.01] + [2.0]*355
        m = json.loads(encode_scan(scan_message(raw, 1, 0.1, 2*math.pi, 0.05, 10)))
        self.assertEqual(len(m['ranges']), 360)
        self.assertEqual(m['ranges'][-5:], [None]*5)
        self.assertEqual(m['ranges'][0], 2)
        self.assertAlmostEqual(m['angle_min'], math.radians(-179.5))
        self.assertAlmostEqual(m['angle_max'], math.radians(179.5))
        self.assertAlmostEqual(m['angle_min']+359*m['angle_increment'], m['angle_max'])
        self.assertEqual(period_ms(15, 10), 70)
        self.assertEqual(period_ms(10, 10), 100)

    def test_acquisition_cadence(self):
        from sensors import Sensors
        class Device:
            def enable(self, ms): self.ms = ms
            def enablePointCloud(self): pass
            def getWidth(self): return 640
            def getHeight(self): return 480
            def getSamplingPeriod(self): return self.ms
            def getHorizontalResolution(self): return 360
            def getFov(self): return 2*math.pi
            def getMinRange(self): return .05
            def getMaxRange(self): return 10
            def getRangeImage(self): return [2]*360
        class Robot:
            def getDevice(self, name): return Device()
        sensors = Sensors(Robot(), 10)
        scans = [sensors.poll(t/100) for t in range(1, 101)]
        scans = [m for m in scans if m]
        self.assertEqual([m['sequence'] for m in scans], list(range(1, 11)))
        self.assertEqual([m['timestamp'] for m in scans], [i/10 for i in range(1, 11)])


class Network(unittest.TestCase):
    def test_slow_client_queue_and_timeout(self):
        from streaming import ScanServer, latest
        async def check():
            server = ScanServer()
            class SlowSocket:
                def __init__(self):
                    self.closed = asyncio.Event()
                    self.code = None
                async def send(self, payload):
                    await asyncio.sleep(10)
                async def close(self, code, reason):
                    self.code = code
                    self.closed.set()
                async def wait_closed(self):
                    await self.closed.wait()
            socket = SlowSocket()
            task = asyncio.create_task(server._client(socket))
            await asyncio.sleep(0)
            pending = next(iter(server.clients))
            latest(pending, 'first')
            await asyncio.sleep(0.01)
            for i in range(100):
                latest(pending, str(i))
            self.assertEqual(pending.qsize(), 1)
            self.assertEqual(pending.get_nowait(), '99')
            await asyncio.wait_for(task, 2)
            self.assertEqual(socket.code, 1013)
            self.assertFalse(server.clients)
            q = queue.Queue(maxsize=2)
            for i in range(10000): latest(q, i)
            self.assertEqual([q.get_nowait(), q.get_nowait()], [9998, 9999])
        asyncio.run(check())

    def test_bounded_reconnect_and_no_client(self):
        from streaming import ScanServer, latest
        from websockets.asyncio.client import connect
        q = queue.Queue(maxsize=2)
        for i in range(100): latest(q, i)
        self.assertEqual([q.get_nowait(), q.get_nowait()], [98, 99])
        server = ScanServer(port=0)
        server.start()
        self.assertTrue(server.ready.wait(3))
        if server.error: raise server.error
        async def check():
            url = f'ws://127.0.0.1:{server.bound_port}'
            for round_ in range(2):
                async with connect(url) as socket:
                    for i in range(1, 4):
                        seq = round_*3+i
                        server.publish(encode_scan(scan_message([2]*360, seq, seq/10,
                                                               2*math.pi, .05, 10)))
                        m = json.loads(await asyncio.wait_for(socket.recv(), 2))
                        self.assertEqual(m['sequence'], seq)
                        self.assertEqual(m['timestamp'], seq/10)
                        self.assertEqual(len(m['ranges']), 360)
            # Producer remains bounded when nobody consumes scans.
            for _ in range(10000): server.publish('{}')
            self.assertLessEqual(server.inbox.qsize(), 2)
        try: asyncio.run(check())
        finally: server.close()
        self.assertFalse(server.thread.is_alive())


if __name__ == '__main__': unittest.main()
