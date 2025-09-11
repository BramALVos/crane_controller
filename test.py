import unittest
from crane_controller import *


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

class CranePathTest(unittest.TestCase):
    def test_speed(self):
        with self.assertRaises(ValueError):
            _ = CranePath(Size(1,1,1), 1001, 1)

        with self.assertRaises(ValueError):
            _ = CranePath(Size(1,1,1), 0, 1)

        with self.assertRaises(ValueError):
            _ = CranePath(Size(1,1,1), 1, 1001)

        with self.assertRaises(ValueError):
            _ = CranePath(Size(1,1,1), 1, 0)

    def test_check_position(self):
        path = CranePath(Size(2, 2, 2), 1, 1)
        with self.assertRaises(ValueError):
            path._check_position(Position(2,0,0))

        with self.assertRaises(ValueError):
            path._check_position(Position(0,3,0))

        with self.assertRaises(ValueError):
            path._check_position(Position(0,0,2))

        with self.assertRaises(ValueError):
            path._check_position(Position(0,0,-1))

    def test_cmds(self):
        path = CranePath(Size(2, 2, 2), 1, 1)
        path.move_to(Position(0,0,0))
        path.attach()
        path.detach()
        path.idle(1000)
        self.assertEqual(path._cmds, [('M', 0, 1000, Position(0,0,0)),
                                      ('A', 1000, 2000),
                                      ('D', 2000, 3000),
                                      ('I', 3000, 4000)
                                      ])

    def test_idle(self):
        path = CranePath(Size(2, 2, 2), 1, 1)
        with self.assertRaises(ValueError):
            path.idle(0)

    def test_calculate_duration(self):
        path = CranePath(Size(2, 2, 2), 1, 1)
        self.assertEqual(path._calculate_duration(1000), (0, 1000))
