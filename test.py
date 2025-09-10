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


class CraneCmdTest(unittest.TestCase):
    def test_move(self):
        with self.assertRaises(IndexError):
            CraneCmd("MOVE")
            CraneCmd("MOVE", blabla=Position(0,0,0))

        with self.assertRaises(TypeError):
            CraneCmd("MOVE", position="blabla")

        cmd = CraneCmd("MOVE", position=Position(0, 0, 0))
        self.assertEqual(cmd.cmd, 'M')
        self.assertEqual(cmd.position, Position(0,0,0))

    def test_idle(self):
        with self.assertRaises(IndexError):
            CraneCmd("IDLE")
            CraneCmd("IDLE", blabla=Position(0,0,0))

        with self.assertRaises(TypeError):
            CraneCmd("IDLE", duration="blabla")

        cmd = CraneCmd("IDLE", duration=1000)
        self.assertEqual(cmd.cmd, 'I')
        self.assertEqual(cmd.duration, 1000)

    def test_attach(self):
        cmd = CraneCmd("ATTACH")
        self.assertEqual(cmd.cmd, 'A')

    def test_detach(self):
        cmd = CraneCmd("DETACH")
        self.assertEqual(cmd.cmd, 'D')
