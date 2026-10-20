"""Check that Webots' +X viewing axis points at the indoor room."""
import math
from pathlib import Path
import re
import unittest


class StartingView(unittest.TestCase):
    def test_view_faces_room_center(self):
        world = (Path(__file__).resolve().parents[1] / 'worlds/indoor.wbt').read_text()
        viewpoint = re.search(r'Viewpoint\s*\{([^}]+)\}', world).group(1)
        axis_and_angle = re.search(r'orientation\s+([\d.eE+\- ]+)', viewpoint).group(1)
        x, y, z, angle = map(float, axis_and_angle.split())
        position = list(map(float, re.search(r'position\s+([\d.eE+\- ]+)', viewpoint).group(1).split()))
        length = math.sqrt(x*x + y*y + z*z)
        x, y, z = x/length, y/length, z/length
        c, s = math.cos(angle), math.sin(angle)
        forward = (c+x*x*(1-c), z*s+y*x*(1-c), -y*s+z*x*(1-c))
        distance = math.sqrt(sum(v*v for v in position))
        alignment = sum(f * -p/distance for f, p in zip(forward, position))
        self.assertGreater(alignment, 0.999, 'Starting viewpoint must face the room center')


if __name__ == '__main__':
    unittest.main()
