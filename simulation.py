#!/usr/bin/env python3


import threading
import time

try:
    import pyray as rl
except ImportError as e:
    print(e)
    print("Please install `raylib` using pip!")
    exit(1)


class Vec3i:
    def __init__(self, x: int, y: int, z: int):
        self.x = int(x)
        self.y = int(y)
        self.z = int(z)

    def __repr__(self):
        return f"[x: {self.x}, y: {self.y}, z: {self.z}]"

    def __floordiv__(self, divider):
        return Vec3i(self.x // divider, self.y // divider, self.z // divider)

    def abs(self):
        return Vec3i(abs(self.x), abs(self.y), abs(self.z))

    def bounds(self, other) -> bool:
        if (other.x >= self.x
            and other.y >= self.y
            and other.z >= self.z):
            return True

        return False


# adapted from https://en.wikipedia.org/wiki/Smoothstep
def clamp(x: float, lowerlimit: float=0.0, upperlimit: float=1.0):
    return (lowerlimit if x < lowerlimit 
            else (upperlimit if x > upperlimit 
            else x))

# adapted from: https://en.wikipedia.org/wiki/Smoothstep
def smoothstep(edge0: float, edge1: float, x: float):
    x = clamp((x - edge0) / (edge1 - edge0))
    return (x ** 2) * (3 - 2 * x) # 3x^2 + 2x^3

class CraneCmd:
    def __init__(self, cmd: str, *args, **kwargs):
        if not cmd.isalpha():
            raise TypeError("cmd should be one of the following strings:\n"
                            "    ATTACH\n"
                            "    DETACH\n"
                            "    IDLE\n"
                            "    MOVE\n")
    
        cmd.upper()
    
        match cmd:
            case "ATTACH":
                self.cmd = 'A'
            case "DETACH":
                self.cmd = 'D'
            case "IDLE":
                if not "duration" in kwargs:
                    raise IndexError("idle command needs a keyword argument "
                                     "`duration` is ms\nFor example:\n"
                                     "crane_cmd(\"IDLE\", duration=1000")
    
                if type(kwargs["duration"]) != int:
                    raise IndexError("idle command duration has to be of type "
                                     "`int`\nFor example:\n"
                                     "crane_cmd(\"IDLE\", duration=1000")
    
                self.cmd = 'I'
                self.duration = kwargs["duration"]
            case "MOVE":
                if not "position" in kwargs:
                    raise IndexError("move command needs a keyword argument "
                                     "`position`\nFor example:\n"
                                     "crane_cmd(\"MOVE\", position=Vec3i(0,0,0)")
    
                if type(kwargs["position"]) != Vec3i:
                    raise IndexError("move command position has to be of type "
                                     "`Vec3i`\nFor example:\n"
                                     "crane_cmd(\"MOVE\", position=Vec3i(0,0,0)")
    
                self.cmd = 'M' 
                self.position = kwargs["position"]
            case _:
                raise TypeError("cmd should be one of the following strings:\n"
                            "    ATTACH\n"
                            "    DETACH\n"
                            "    IDLE\n"
                            "    MOVE\n")

    def __repr__(self) -> str:
        match self.cmd:
            case 'M':
                return f"CraneCmd: MOVE {self.position}"
            case 'I':
                return f"CraneCmd: IDLE {self.duration} s"
            case 'A':
                return f"CraneCmd: ATTACH"
            case _:
                return f"CraneCmd: DETACH"


class CraneControler:
    def __init__(self, warehouse_size: Vec3i):
        self.cmd_lock = threading.Lock()
        self.cmd_list: list[tuple[CraneCmd, int, int]] = []
        self.speed = [1, 1, 1]
        self.plane = warehouse_size
        self.plane.x += 1
        self.plane.y += 2
        self.containers: list[list[int]] = []
        self.attached_container = False

        self._engine_shutdown = False
        self._inactive_simulation = threading.Event()
        self._inactive_simulation.set()
        self._start_time: int = 0
        self._engine_thread = threading.Thread(target=CraneControler._engine_run, 
                                               args=(self,), 
                                               kwargs={})

    def __enter__(self):
        self._engine_thread.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self._engine_shutdown = True
        if self._engine_is_running:
            self._engine_thread.join()


    def _engine_run(self):
        self._engine_is_running = True
        rl.set_trace_log_level(rl.TraceLogLevel.LOG_WARNING)
        rl.init_window(1280, 720, "Test")
        rl.set_target_fps(60)

        camera = rl.Camera3D()
        camera.position = rl.Vector3(10., 10., 10.)
        camera.target=rl.Vector3(0, 0, 0)
        camera.up=rl.Vector3(0, 1., 0)
        camera.fovy=45.0
        camera.projection = rl.CameraProjection.CAMERA_PERSPECTIVE

        self.pole_size: float = 0.25
        self.pole_distance_multiplier: float = 0.5

        self.crane_starting_pos = Vec3i(0, 0, 0)

        rl.disable_cursor()

        current_cmd = None
        current_pos = rl.Vector3(self.crane_starting_pos.x,
                                 self.crane_starting_pos.y,
                                 self.crane_starting_pos.z)

        self.delta_time: int = 0

        while not rl.window_should_close() and not self._engine_shutdown:
            rl.update_camera(camera, rl.CameraMode.CAMERA_THIRD_PERSON)
            #rl.set_mouse_position(1280 // 2, 720 // 2)

            if not self._inactive_simulation.is_set():
                with self.cmd_lock:
                    current_cmd = self.cmd_list[0] if len(self.cmd_list) > 0 else None

                    if current_cmd is not None:
                        time_index = (time.time_ns() // 1000_000) - self._start_time
                        if time_index >= current_cmd[2]:
                            self._exec_till_cmd_index(time_index)
                            # self.cmd_list.pop(0)
                            if len(self.cmd_list) == 0:
                                self._inactive_simulation.set()
                                continue

                            current_cmd = self.cmd_list[0]
                        match current_cmd[0].cmd:
                            case 'M':
                                i = smoothstep(current_cmd[1], 
                                               current_cmd[2], 
                                               time_index)

                                current_pos = rl.Vector3(self.crane_starting_pos.x,
                                                         self.crane_starting_pos.y,
                                                         self.crane_starting_pos.z)

                                current_pos.x += (current_cmd[0].position.x -
                                                  self.crane_starting_pos.x) * i
                                current_pos.y += (current_cmd[0].position.y -
                                                  self.crane_starting_pos.y) * i
                                current_pos.z += (current_cmd[0].position.z -
                                                  self.crane_starting_pos.z) * i


                            case 'I':
                                ...
                            case _:
                                ...
                    else:
                        self._inactive_simulation.set()




            rl.begin_drawing()
            rl.clear_background(rl.WHITE)
            rl.draw_text(f"fps: {rl.get_fps()}", 10, 10, 20, rl.GRAY)
            rl.draw_text("Crane visualizer by Bram Vos", 10, 700, 14, rl.GRAY)
            rl.begin_mode_3d(camera)

            self.draw_crane(current_pos)
            self.draw_containers()


            rl.draw_grid(10, 1.)

            rl.end_mode_3d()
            rl.end_drawing()

        rl.close_window()
        self._inactive_simulation.set()
        self._engine_is_running = False

    def _exec_till_cmd_index(self, t):
        index = self._find_cmd_index(t)
        self._exec_cmd_range(index if index > 0 else 1, t)

    def _find_cmd_index(self, index: int):
        l = 0
        r = len(self.cmd_list) - 1
        while l <= r:
            m = (r + l) // 2
            if self.cmd_list[m][1] == index:
                return m

            if self.cmd_list[m][1] < index:
                l = m + 1
            elif self.cmd_list[m][1] > index:
                r = m - 1

        return (r + l) // 2

    def _exec_cmd_range(self, end: int, t):
        for _ in range(end):
            print(f"{self.cmd_list[0][0]} @ t = {t} ms")
            match self.cmd_list[0][0].cmd:
                case 'M':
                    self.crane_starting_pos = self.cmd_list[0][0].position
                case 'A':
                    if not self._attach_container(self.crane_starting_pos):
                        self._inactive_simulation.set()
                        print("Failed to attach container!")
                case 'D':
                    if not self._detach_container(self.crane_starting_pos):
                        self._inactive_simulation.set()
                        print("Failed to detach container!")
                case 'I':
                    ...

            self.cmd_list.pop(0)

    def draw_containers(self):
        for iz, z in enumerate(self.containers):
            for ix, x in enumerate(z):
                for y in range(x):
                    pos = rl.Vector3(ix + 1, y + 0.5, iz + 0.5)
                    size = rl.Vector3(1, 1, 1)
                    rl.draw_cube_v(pos, size, rl.BLUE)
                    rl.draw_cube_wires_v(pos, size, rl.SKYBLUE)

    def draw_crane(self, position: rl.Vector3):
        self._draw_crane_frame(position)
        self._draw_crane_top(position)
        self._draw_crane_hook(position)
        self._draw_crane_container(position)

    def _draw_crane_frame(self, position: rl.Vector3):
        for x in range(0, 2):
            for z in range(-1, 2, 2):
                pos = rl.Vector3(
                    x * (self.plane.x),
                    self.plane.y / 2,
                    (position.z) + z * self.pole_distance_multiplier + 0.5,
                )
                size = rl.Vector3(self.pole_size, self.plane.y, self.pole_size)
                rl.draw_cube_v(pos, size, rl.YELLOW)

                pos.x = 0.5 * (self.plane.x)
                pos.y = self.plane.y + self.pole_size / 2
                size.x = self.plane.x + self.pole_size
                size.y = self.pole_size
                rl.draw_cube_v(pos, size, rl.ORANGE)

    def _draw_crane_top(self, position: rl.Vector3):
        pos = rl.Vector3(
            position.x + 1,
            self.plane.y,
            position.z + 0.5
        )
        size = rl.Vector3(1.5, 0.5, 1 - self.pole_size)
        rl.draw_cube_v(pos, size, rl.RED)

    def _draw_crane_hook(self, position: rl.Vector3):
        pos = rl.Vector3(
            position.x + 1,
            position.y + 1.1,
            position.z + 0.5
        )
        size = rl.Vector3(0.25, 0.2, 0.25)
        rl.draw_cube_v(pos, size, rl.RED)
        size.y = (self.plane.y - pos.y)
        pos.y = size.y / 2 + pos.y
        size.x = size.z = 0.05
        rl.draw_cube_v(pos, size, rl.RED)

    def _draw_crane_container(self, position: rl.Vector3):
        if self.attached_container:
            pos = rl.Vector3(
                position.x + 1,
                position.y + 0.5,
                position.z + 0.5
            )
            size = rl.Vector3(1, 1, 1)
            rl.draw_cube_v(pos, size, rl.BLUE)
            rl.draw_cube_wires_v(pos, size, rl.RED)


    def check_coords(self, coords: Vec3i) -> None:
        if coords.x + 1 >= self.plane.x:
            raise ValueError("invalid x dimention")
        if coords.y + 1 >= self.plane.y:
            raise ValueError("invalid y dimention")
        if coords.z >= self.plane.z:
            raise ValueError("invalid x dimention")

    def _detach_container(self, pos: Vec3i) -> bool:
        if self.containers[pos.x][pos.z] != pos.y:
            return False

        self.containers[pos.x][pos.z] += 1
        self.attached_container = False
        return True

    def _attach_container(self, pos: Vec3i) -> bool:
        if self.containers[pos.x][pos.z] - 1 != pos.y:
            return False

        self.containers[pos.x][pos.z] -= 1
        self.attached_container = True
        return True


    def append_cmds(self, *args):
        """
        push instructions to the instruction stack
        this instruction stack will be read by the engine after
        `start_execution` has been called

        The time duration will of these commands will be handled 
        in this function
        """
        with self.cmd_lock:
            for arg in args:
                t_start = 0
                if len(self.cmd_list) > 0:
                    t_start = self.cmd_list[-1][2]

                if type(arg) != CraneCmd:
                    raise TypeError("All arguments should be of type "
                                    "`CraneCmd`\nExample:\n"
                                    "CraneCmd(\"MOVE\", position=Vec3i(0,0,0)")

                t_end = t_start
                match arg.cmd:
                    case 'I':
                        t_end = t_start + arg.duration
                    case 'A':
                        t_end = t_start + self.speed[2] * 1000
                    case 'D':
                        t_end = t_start + self.speed[2] * 1000
                    case 'M':
                        self.check_coords(arg.position)
                        t_end = t_start + self.speed[0] * 1000

                self.cmd_list.append((arg, t_start, t_end))


    def exec(self):
        self._start_time = time.time_ns() // 1000_000
        self._inactive_simulation.clear()
        self._inactive_simulation.wait()

    def set_move_speed(self, speed):
        self.speed[0] = 1/speed

    def fill_warehouse(self, *args):
        if len(args) > self.plane.x - 1:
            raise ValueError(f"invalid x dimention!")

        for arg in args:
            if type(arg) != list:
                raise TypeError("not a list!")
            elif len(arg) > self.plane.z:
                raise ValueError(f"too thick {len(arg)} - {self.plane.z}")
            for a in arg:
                if a > (self.plane.y - 1):
                    raise ValueError(f"to high")
            self.containers.append(arg)



def main() -> int:
    vector: Vec3i = Vec3i(1, 2, 3)
    print(vector)

    with CraneControler(Vec3i(4, 3, 4)) as crane:
        crane.set_move_speed(1)
        crane.fill_warehouse(
            [1, 1, 3, 3],
            [3, 3, 2, 1],
            [2, 2, 2, 2],
            [3, 1, 1, 1],
        )
        while True:
            crane.append_cmds(
                CraneCmd('MOVE', position=Vec3i(0,0,0)),
                CraneCmd("ATTACH"),
                CraneCmd('MOVE', position=Vec3i(0,3,0)),
                CraneCmd('MOVE', position=Vec3i(3,3,3)),
                CraneCmd('MOVE', position=Vec3i(3,1,3)),
                CraneCmd('DETACH'),
                CraneCmd('MOVE', position=Vec3i(3,3,3)),
                CraneCmd("IDLE", duration=2000)
            )
            crane.exec()

    return 0


if __name__ == '__main__':
    exit(main())
