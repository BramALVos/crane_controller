#!/usr/bin/env python3

from crane_controller import *

def main():
    warehouse_size = Size(4, 3, 4)

    moving_speed = 1
    attach_and_detach_speed = 1

    path: CranePath = CranePath(warehouse_size, moving_speed, 
                                attach_and_detach_speed)

    with CraneController(warehouse_size) as crane:

        crane.fill_warehouse(
            [1, 1, 3, 3],
            [3, 3, 2, 1],
            [2, 2, 2, 2],
            [3, 1, 1, 1],
        )

        (path.move_to(Position(0,0,0))
             .attach()
             .move_to(Position(0,3,0))
             .move_to(Position(3,3,3))
             .move_to(Position(3,1,3))
             .detach()
             .move_to(Position(3,3,3))
             .idle(2000)
             .move_to(Position(0,3,0)))

        crane.exec(path)


if __name__ == '__main__':
    main()
