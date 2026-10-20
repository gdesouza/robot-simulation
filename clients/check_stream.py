#!/usr/bin/env python3
"""Verify consecutive live scans. Run while the Webots world is playing."""
import argparse
import asyncio
import json
import math
from websockets.asyncio.client import connect


async def check(url, count, samples):
    previous = None
    async with connect(url) as socket:
        for _ in range(count):
            message = json.loads(await asyncio.wait_for(socket.recv(), 5),
                                 parse_constant=lambda value: (_ for _ in ()).throw(
                                     ValueError(f'Invalid JSON constant: {value}')))
            assert message['type'] == 'lidar_scan'
            assert message['schema_version'] == 1
            assert message['frame_id'] == 'lidar'
            assert len(message['ranges']) == samples
            assert math.isfinite(message['timestamp'])
            assert message['angle_increment'] > 0
            assert math.isclose(message['angle_min'] + (samples-1)*message['angle_increment'],
                                message['angle_max'], abs_tol=1e-8)
            assert all(v is None or (math.isfinite(v) and
                       message['range_min'] <= v <= message['range_max'])
                       for v in message['ranges'])
            if previous:
                assert message['sequence'] > previous['sequence']
                assert message['timestamp'] > previous['timestamp']
            previous = message
    print(f'PASS: {count} scans, {samples} samples; last sequence '
          f'{previous["sequence"]}, sim time {previous["timestamp"]:.3f} s')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='ws://127.0.0.1:8765')
    parser.add_argument('--count', type=int, default=20)
    parser.add_argument('--samples', type=int, default=360)
    args = parser.parse_args()
    if args.count < 1 or args.samples < 1:
        parser.error('count and samples must be positive')
    asyncio.run(check(args.url, args.count, args.samples))
