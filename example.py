#!/usr/bin/env python3

from simulation import *

def main() -> int:
    vector: Position = Position(1, 2, 3)
    print(vector)

    with CraneController(Size(4, 3, 4)) as crane:
        crane.set_move_speed(1)
        crane.fill_warehouse(
            [1, 1, 3, 3],
            [3, 3, 2, 1],
            [2, 2, 2, 2],
            [3, 1, 1, 1],
        )
        while True:
            crane.append_cmds(
                CraneCmd('MOVE', position=Position(0,0,0)),
                CraneCmd("ATTACH"),
                CraneCmd('MOVE', position=Position(0,3,0)),
                CraneCmd('MOVE', position=Position(3,3,3)),
                CraneCmd('MOVE', position=Position(3,1,3)),
                CraneCmd('DETACH'),
                CraneCmd('MOVE', position=Position(3,3,3)),
                CraneCmd("IDLE", duration=2000)
            )
            crane.exec()


if __name__ == '__main__':
    exit(main())

