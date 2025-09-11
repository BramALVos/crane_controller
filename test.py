import unittest
from simulation import *


class Vec3iTest(unittest.TestCase):
    def test_fields(self):
        vec: Vec3i = Vec3i(1602, 6502, 80)
        self.assertEqual(vec.x, 1602)
        self.assertEqual(vec.y, 6502)
        self.assertEqual(vec.z, 80)

    def test_repr(self):
        vec: Vec3i = Vec3i(1, 2, 3)
        self.assertEqual(f"{vec}", "Vec3i[x: 1, y: 2, z: 3]")

    def test_eq(self):
        vec1: Vec3i = Vec3i(1, 1, 1)
        vec2: Vec3i = Vec3i(1, 1, 2)
        self.assertNotEqual(vec1, vec2)
        vec2.z = 1
        self.assertEqual(vec1, vec2)


class SmoothstepTest(unittest.TestCase):
    def test_clamp(self):
        self.assertEqual(clamp(-1.0), 0)
        self.assertEqual(clamp(2.0), 1)
        self.assertEqual(clamp(0.5), 0.5)
        self.assertEqual(clamp(-2, lower_limit=-1.0), -1.0)
        self.assertEqual(clamp(3, upper_limit=2.0), 2.0)

    def test_smoothstep(self):
        self.assertEqual(smoothstep(0, 1, 0), 0)
        self.assertEqual(smoothstep(0, 1, 1), 1)
        self.assertEqual(smoothstep(0, 1, 0.5), 0.5)
        # TODO: add more test cases!

