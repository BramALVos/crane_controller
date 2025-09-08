R"""
  ____ ____      _    _   _ _____
 / ___|  _ \    / \  | \ | | ____|
| |   | |_) |  / _ \ |  \| |  _|
| |___|  _ <  / ___ \| |\  | |___
 \____|_| \_\/_/   \_\_| \_|_____|
  ____ ___  _   _ _____ ____   ___  _     _     _____ ____
 / ___/ _ \| \ | |_   _|  _ \ / _ \| |   | |   | ____|  _ \
| |  | | | |  \| | | | | |_) | | | | |   | |   |  _| | |_) |
| |__| |_| | |\  | | | |  _ <| |_| | |___| |___| |___|  _ <
 \____\___/|_| \_| |_| |_| \_\\___/|_____|_____|_____|_| \_\

A Python module for simulating the movement of a warehouse crane and the 
interaction of containers.

For examples on how to use this module see `example.py`

Licence: MIT

Copyright (c) 2025 Bram Vos (vos0127@hz.nl)
Copyright (c) 2025 gwaadiegwaa

THIS CODE COMES WITH NO WARRANTY.
USE AT YOUR OWN RISK!
"""

import threading
import time

try:
    import pyray as rl
except ImportError as e:
    print(e)
    print("Please install `raylib` using pip! (`pip install raylib`)")
    exit(1)


class Vec3i:
    """
    3D Integer vector class
    This class serves as the baseclass for the Position and Size class
    """ 
    def __init__(self, x: int, y: int, z: int):
        """
        Initialize an Vec3i
        Parameters:
            x (int): The x value of the vector
            y (int): The y value of the vector
            z (int): The z value of the vector
        Returns:
            A new Vec3i with the passed values for x, y and z
        """
        self.x = int(x)
        self.y = int(y)
        self.z = int(z)

    def __repr__(self):
        """
        Return a string representation of an Vec3i or a child of Vec3i
        """
        return (f"{self.__class__.__name__}"
                f"[x: {self.x}, y: {self.y}, z: {self.z}]")

    def __eq__(self, other):
        """
        Compare two Vec3i's
        Parameters:
            other (Vec3i): the Vec3i to compare to self
        Returns:
            True when self is equal to other, else return False
        """
        return self.x == other.x and self.y == other.y and self.z == other.z


class Position(Vec3i):
    """
    A position in the 3D space of the warehouse.
    This class is a child of Vec3i
    """
    ...

class Size(Vec3i):
    """
    A 3D size.
    This class is a child of Vec3i
    """
    ...

def clamp(x: float, lower_limit: float=0.0, upper_limit: float=1.0):
    """
    clamp a value between two points
    Parameters:
        x (float): The value to be clamped
        lower_limit (float): The lower_limit of the clamp function 
                             (aka the lowest possible value)
                             Default value = 0.0

        upper_limit (float): The upper_limit of the clamp function 
                             (aka the biggest possible value)
                             Default value = 1.0

    Returns:
        x or lower_limit when x < lower_limit or upper_limit
        when x > upper_limit
    """
    return min(max(x, lower_limit), upper_limit)

# adapted from: https://en.wikipedia.org/wiki/Smoothstep
def smoothstep(edge0: float, edge1: float, x: float):
    """
    return a value between 0 and 1 with a smooth transition at the beginning 
    and end.

    Parameters:
        edge0 (float): The lowest value that x can be
        edge1 (float): The biggest value that x can be
        x (float): The value to be used in the smoothstep function

    Returns:
        3x^2 - 2x^3 where x has been clamped with the help of edge0 and edge1
    """
    x = clamp((x - edge0) / (edge1 - edge0))
    return (3 - 2 * x) * (x ** 2)   # 3x^2 - 2x^3


class CraneCmd:
    """
    A structure which contains one of the supported commands for the crane
    It is used by the CraneController.append_cmds() function
    As a first layer of typechecking
    """

    def __init__(self, cmd: str, **kwargs):
        """
        Create a CraneCmd

        Parameters:
            cmd (str): A valid command. Valid commands are:
                       "ATTACH"
                       "DETACH"
                       "MOVE"
                       "IDLE"
        kwargs dict[str, any]: An extra argument. Only used with MOVE and IDLE
                               MOVE needs a position kw argument as a Position
                               IDLE needs a duration kw argument as an int
        Returns:
            A valid CraneCmd
        Raises:
            when an invalid command is given or a kw argument is missing for
            the MOVE or the IDLE command
        """
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
                    raise TypeError("idle command duration has to be of type "
                                     "`int`\nFor example:\n"
                                     "crane_cmd(\"IDLE\", duration=1000")
    
                self.cmd = 'I'
                self.duration = kwargs["duration"]
            case "MOVE":
                if not "position" in kwargs:
                    raise IndexError("move command needs a keyword argument "
                                     "`position`\nFor example:\n"
                                     "crane_cmd(\"MOVE\", position=Position(0,0,0)")
    
                if type(kwargs["position"]) != Position:
                    raise TypeError("move command position has to be of type "
                                     "`Position`\nFor example:\n"
                                     "crane_cmd(\"MOVE\", position=Position(0,0,0)")
    
                self.cmd = 'M' 
                self.position = kwargs["position"]
            case _:
                raise TypeError("cmd should be one of the following strings:\n"
                            "    ATTACH\n"
                            "    DETACH\n"
                            "    IDLE\n"
                            "    MOVE\n")

    def __repr__(self) -> str:
        """
        Returns a string representation of a CraneCmd
        """
        match self.cmd:
            case 'M':
                return f"CraneCmd: MOVE {self.position}"
            case 'I':
                return f"CraneCmd: IDLE {self.duration} s"
            case _:
                return "CraneCmd: " + ("DETACH" if self.cmd == 'D' 
                                                else "ATTACH")



class CraneController:
    """
    This class is responsible for setting up / running a simulation
    It spawns a render thread and is controlled by the main thread
    This makes it possible to keep the window alive while doing other stuff
    """
    def __init__(self, warehouse_size: Size):
        """
        Initialize controller and spawn the render thread
        Parameters:
            warehouse_size (Size): the size of the warehouse (how many blocks 
                                   should fit in the x, y and z directions)
        Returns:
            A ready to use CraneController (yay!)
        """
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
        self._engine_thread = threading.Thread(target=CraneController._engine_run,
                                               args=(self,),
                                               kwargs={})

    def __enter__(self):
        """
        This function forces the user to use CraneController with a with 
        statement (not really, but it makes it harder). This is needed since 
        raylib (responsible for all the graphics needs to be 
        deinitialized when the window closes.
        A with statement makes sure that __exit__ will get called and __exit__ 
        will close the window respectfully
        """
        self._engine_thread.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        """
        This function will get called when we exit the with statement which 
        houses the CraneController (see __enter__ for more information)
        """
        self._engine_shutdown = True
        if self._engine_is_running:
            self._engine_thread.join()


    def _engine_run(self):
        """
        This method is responsible for all the rendering and is run as a 
        separate thread.
        It displays the graphics and will execute (through helper functions) 
        the commands or display them (in the case of MOVE)
        """
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

        self.crane_starting_pos = Position(0, 0, 0)

        rl.disable_cursor()

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

    def _exec_till_cmd_index(self, t: int):
        """
        Execute commands till a certain time
        This function is needed when commands need to be executed faster than
        the frame rate. This function will execute the commands which have been
        missed almost instantly.
        Parameters:
            t (int): time in ms since exec has been called
        Returns:
            None
        """
        index = self._find_cmd_index(t)
        self._exec_cmd_range(index if index > 0 else 1, t)

    def _find_cmd_index(self, index: int):
        """
        Figure out which command has to be executed currently
        This is basically binary search with a fancy name :)
        Parameters:
            index (int): a time index into the array of commands in ms
        Returns:
            The index of the current command as an int
        """
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

    def _exec_cmd_range(self, end: int, t: int):
        """
        Execute all the commands from the currently processed command till 
        the command which starts at time t
        Parameters:
            end (int): index to the last command to be executed
            t (int): current time since exec has been called in ms
        Returns:
            None
        Effects:
            The active simulation status.
            When a container can not be attached or detached it will halt the
            simulation
        """
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
        """
        Draw the containers in the warehouse as a cube
        """
        for iz, z in enumerate(self.containers):
            for ix, x in enumerate(z):
                for y in range(x):
                    pos = rl.Vector3(ix + 1, y + 0.5, iz + 0.5)
                    size = rl.Vector3(1, 1, 1)
                    rl.draw_cube_v(pos, size, rl.BLUE)
                    rl.draw_cube_wires_v(pos, size, rl.SKYBLUE)

    def draw_crane(self, position: rl.Vector3):
        """
        Draw the crane at a certain position in the warehouse
        Parameters:
            position (rl.Vector3): The position of the crane
        Returns:
            None
        """
        self._draw_crane_frame(position)
        self._draw_crane_top(position)
        self._draw_crane_hook(position)
        self._draw_crane_container(position)

    def _draw_crane_frame(self, position: rl.Vector3):
        """
        Draw the frame of the crane at a certain position in the warehouse
        Parameters:
            position (rl.Vector3): The position of the crane (which effects 
            the positioning of the frame
        Returns:
            None
        """
        for x in range(0, 2):
            for z in range(-1, 2, 2):
                pos = rl.Vector3(
                    x * self.plane.x,
                    self.plane.y / 2,
                    position.z + z * self.pole_distance_multiplier + 0.5,
                )
                size = rl.Vector3(self.pole_size, self.plane.y, self.pole_size)
                rl.draw_cube_v(pos, size, rl.YELLOW)

                pos.x = 0.5 * self.plane.x
                pos.y = self.plane.y + self.pole_size / 2
                size.x = self.plane.x + self.pole_size
                size.y = self.pole_size
                rl.draw_cube_v(pos, size, rl.ORANGE)

    def _draw_crane_top(self, position: rl.Vector3):
        """
        Draw the top of the crane at a certain position in the warehouse
        Parameters:
            position (rl.Vector3): The position of the crane (which effects 
            the positioning of the top of the crane
        Returns:
            None
        """
        pos = rl.Vector3(
            position.x + 1,
            self.plane.y,
            position.z + 0.5
        )
        size = rl.Vector3(1.5, 0.5, 1 - self.pole_size)
        rl.draw_cube_v(pos, size, rl.RED)

    def _draw_crane_hook(self, position: rl.Vector3):
        """
        Draw the hook and rope of the crane at a certain position in
        the warehouse
        Parameters:
            position (rl.Vector3): The position of the crane (which effects 
            the positioning of the hook and the rope of the crane
        Returns:
            None
        """
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
        """
        Draw the container hanging on the hook of the crane at a position when 
        there is a hanging container.
        Parameters:
            position (rl.Vector3): The position of the crane (which effects 
            the positioning of the hanging container (when there is one)
        Returns:
            None
        """
        if self.attached_container:
            pos = rl.Vector3(
                position.x + 1,
                position.y + 0.5,
                position.z + 0.5
            )
            size = rl.Vector3(1, 1, 1)
            rl.draw_cube_v(pos, size, rl.BLUE)
            rl.draw_cube_wires_v(pos, size, rl.RED)


    def check_coord(self, coord: Position) -> None:
        """
        Determine if a coordinate is valid (aka does it fit in the warehouse)
        Parameters:
            coord (Position): The coordinate to be checked
        Returns:
            None
        Raises:
            a ValueError when the coordinate is not inside the warehouse
        """
        if coord.x + 1 >= self.plane.x:
            raise ValueError("invalid x dimension")
        if coord.y + 1 >= self.plane.y:
            raise ValueError("invalid y dimension")
        if coord.z >= self.plane.z:
            raise ValueError("invalid x dimension")

    def _detach_container(self, pos: Position) -> bool:
        """
        Try to detach a container a when the hook is a certain position
        Parameters:
            pos (Position): The position of the crane hook
        Returns:
            True when a container could be detached else False
        """
        if self.containers[pos.x][pos.z] != pos.y:
            return False

        self.containers[pos.x][pos.z] += 1
        self.attached_container = False
        return True

    def _attach_container(self, pos: Position) -> bool:
        """
        Try to attach a container a when the hook is a certain position
        Parameters:
            pos (Position): The position of the crane hook
        Returns:
            True when a container could be attached else False
        """
        if self.containers[pos.x][pos.z] - 1 != pos.y:
            return False

        self.containers[pos.x][pos.z] -= 1
        self.attached_container = True
        return True


    def append_cmds(self, *args):
        """
        Append one or more commands to the command list
        Parameters:
            args (tuple[CraneCmd]): A list of CraneCmd's
        Returns:
            None
        Raises:
            A TypeError when args contained something other than CraneCmd
            or a ValueError when the position associated with a MOVE command
            is not inside the warehouse
        """
        with self.cmd_lock:
            for arg in args:
                t_start = 0
                if len(self.cmd_list) > 0:
                    t_start = self.cmd_list[-1][2]

                if type(arg) != CraneCmd:
                    raise TypeError("All arguments should be of type "
                                    "`CraneCmd`\nExample:\n"
                                    "CraneCmd(\"MOVE\", position=Position(0,0,0)")

                t_end = t_start
                match arg.cmd:
                    case 'I':
                        t_end = t_start + arg.duration
                    case 'A':
                        t_end = t_start + self.speed[2] * 1000
                    case 'D':
                        t_end = t_start + self.speed[2] * 1000
                    case 'M':
                        self.check_coord(arg.position)
                        t_end = t_start + self.speed[0] * 1000

                self.cmd_list.append((arg, t_start, t_end))


    def exec(self):
        """
        Execute a list of CraneCmd's supplied to append_cmds
        Raises:
            A ThreadError when the render thread (aka engine thread) has died
        """
        self._start_time = time.time_ns() // 1000_000
        self._inactive_simulation.clear()
        self._inactive_simulation.wait()
        if not self._engine_is_running:
            raise threading.ThreadError("Engine thread stopped")

    def set_move_speed(self, speed):
        """
        Set the move speed of the crane
        Parameters:
            speed (float): The speed of the crane
        TODO:
            add a speed constraint of a 1000
            This function needs attention in general
        """
        self.speed[0] = 1/speed

    def fill_warehouse(self, *args):
        """
        Fill the warehouse with containers
        Parameters:
        args (tuple[list[int]]): A tuple where each element is a list which 
                                 contains integers. The integers represent the 
                                 hight (aka how many boxes are stacked).
                                 each element in the list is the hight for a
                                 certain x position. Each list contains the 
                                 values for x and y where the list is a z 
                                 position. TODO: Clarify with an example
        Returns:
            None
        Raises:
            A ValueError when x, y, or z is not inside the warehouse or a
            TypeError when args contains a type other than list
        """
        if len(args) > self.plane.x - 1:
            raise ValueError(f"invalid x dimension!")

        for arg in args:
            if type(arg) != list:
                raise TypeError("not a list!")
            elif len(arg) > self.plane.z:
                raise ValueError(f"invalid z dimention")
            for a in arg:
                if a > (self.plane.y - 1):
                    raise ValueError(f"invalid y dimention")
            self.containers.append(arg)
