#!/usr/bin/env python3

from simulation import *

def main() -> int:
    vector: Position = Position(1, 2, 3)
    print(vector)

    warehouse_size = Size(4, 3, 4)

    path: CranePath = CranePath(warehouse_size, 100, 1000)

    with CraneController(warehouse_size) as crane:

        for _ in range(10):
            crane.fill_warehouse(
                [1, 1, 3, 3],
                [3, 3, 2, 1],
                [2, 2, 2, 2],
                [3, 1, 1, 1],
            )

            (
            path.move_to(Position(0,0,0))
                .attach()
                .move_to(Position(0,3,0))
                .move_to(Position(3,3,3))
                .move_to(Position(3,1,3))
                .detach()
                .move_to(Position(3,3,3))
                .idle(2000)
                .move_to(Position(0,3,0))
            )

            crane.exec(path)

    return 0


if __name__ == '__main__':
    exit(main())
