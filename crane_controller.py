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

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import threading
import time
from typing import Self
from copy import deepcopy

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
            other (Vec3i): The Vec3i to compare to self
        Returns:
            True when self is equal to other, else return False
        """
        return self.x == other.x and self.y == other.y and self.z == other.z


class Position(Vec3i):
    """
    A position in the 3D space of the warehouse.
    """
    ...

class Size(Vec3i):
    """
    A 3D size.
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


class CranePath:
    """
    This class is used for chaining crane commands.
    They can be passed to CraneController.exec() to execute them
    """
    def __init__(self, warehouse_size: Size, move_speed: int, 
                 attach_detach_speed: int):
        """
        Initialize a CranePath structure.
        Commands can be pushed to this structure later on.
        """
        if not (1 <= move_speed <= 1000):
            raise ValueError("move_speed must be between 1 and 999")
        elif not (1 <= attach_detach_speed <= 1000):
            raise ValueError("attach_detach_speed must be between 1 and 999")

        self._cmds: list[tuple] = []
        self._move_speed = 1001 - move_speed
        self._attach_detach_speed = 1001 - attach_detach_speed
        self._warehouse_size = deepcopy(warehouse_size)
        self._warehouse_size.y += 1

    def __len__(self):
        """
        Return the command count
        """
        return len(self._cmds)

    def _check_position(self, position: Position) -> None:
        """
        Determine if a coordinate is valid (aka does it fit in the warehouse)
        Parameters:
            position (Position): The coordinate to be checked
        Returns:
            None
        Raises:
            a ValueError when the coordinate is not inside the warehouse
        """
        if position.x < 0 or position.y < 0 or position.z < 0:
            raise ValueError("x, y, or z may not be less than 0")
        if position.x >= self._warehouse_size.x:
            raise ValueError("invalid x dimension "
                             f"(max is {self._warehouse_size.x - 2})")
        if position.y >= self._warehouse_size.y:
            raise ValueError("invalid y dimension "
                             f"(max is {self._warehouse_size.y - 2})")
        if position.z >= self._warehouse_size.z:
            raise ValueError("invalid z dimension "
                             f"(max is {self._warehouse_size.z - 1})")

    def attach(self) -> Self:
        """
        Append an attach command. This command wil attach a container 
        to the crane when possible
        """
        self._cmds.append(('A',
                           *self._calculate_duration(self._attach_detach_speed)
                           ))
        return self

    def detach(self) -> Self:
        """
        Append a detach command. This command wil detach a container 
        from the crane when possible
        """
        self._cmds.append(('D', 
                           *self._calculate_duration(self._attach_detach_speed)
                           ))
        return self

    def move_to(self, position: Position) -> Self:
        """
        Append a move command. This command will move the crane to 
        certain position.
        Parameters:
            position (Position): The position to which the crane should move
        Raises:
            A ValueError when an invalid position is given.
        """
        self._check_position(position)
        self._cmds.append(('M', 
                           *self._calculate_duration(self._move_speed),
                           position))
        return self

    def idle(self, duration: int) -> Self:
        """
        Append an idle command. This command will make the crane wait for a 
        duration in ms.
        Parameters:
            duration (int): A duration to wait for in ms
        """
        if duration < 1:
            raise ValueError("duration must be 1 ms or higher")
        self._cmds.append(("I", 
                           *self._calculate_duration(duration)))
        return self

    def _calculate_duration(self, duration: int):
        """
        Calculate the start and end time for a command.
        Parameters:
            duration (int): The duration of the command
        Returns:
            A tuple with the start and end time of the command
        """
        t_start: int = 0
        if len(self._cmds) > 0:
            t_start = self._cmds[-1][2]

        t_end: int = t_start + duration
        return (t_start, t_end)

    def __repr__(self):
        """
        Return the string representation of a CranePath.
        """
        result = ""
        mapping: dict[str, str] = {'M': "MOVE", 'D': "DETACH", 
                                   'A': "ATTACH", 'I': "IDLE"}
        for cmd in self._cmds:
            result += f"{mapping[cmd[0]]}"
            if cmd[0] == 'M':
                result += f" {cmd[3]}"
            elif cmd[0] == 'I':
                result += f" {cmd[2] - cmd[1]}"
            result += f" @ {cmd[1]}\n"
        return result

class CraneController:
    """
    This class is responsible for setting up / running a simulation
    It spawns a render thread and is controlled by the main thread.
    This makes it possible to keep the window alive while doing other stuff.
    """
    def __init__(self, warehouse_size: Size, window_width=1280, 
                 window_height=720, resizeable=False):
        """
        Initialize controller and spawn the render thread
        Parameters:
            warehouse_size (Size): The size of the warehouse (how many blocks 
                                   should fit in the x, y and z directions)
            window_width (int): The width of the window (default 1280 px)
            window_height (int): The height of the window (default 720 px)
        Returns:
            A ready to use CraneController (yay!)
        """
        self.window_width = window_width
        self.window_height = window_height
        self.resizeable = resizeable

        self.cmd_lock = threading.Lock()
        self.cmd_list: list[tuple] = []
        self.speed = [1, 1, 1]
        self.plane = deepcopy(warehouse_size)
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
        rl.init_window(self.window_width, self.window_height, "CraneController")
        rl.set_target_fps(60)
        if self.resizeable:
            rl.set_config_flags(rl.ConfigFlags.FLAG_WINDOW_RESIZABLE)

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


        while not rl.window_should_close() and not self._engine_shutdown:
            rl.update_camera(camera, rl.CameraMode.CAMERA_THIRD_PERSON)
            current_pos = rl.Vector3(self.crane_starting_pos.x,
                                     self.crane_starting_pos.y,
                                     self.crane_starting_pos.z)

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

                        current_pos = rl.Vector3(self.crane_starting_pos.x,
                                                 self.crane_starting_pos.y,
                                                 self.crane_starting_pos.z)
                        match current_cmd[0]:
                            case 'M':
                                i = smoothstep(current_cmd[1], 
                                               current_cmd[2], 
                                               time_index)

                                current_pos.x += (current_cmd[3].x -
                                                  self.crane_starting_pos.x) * i
                                current_pos.y += (current_cmd[3].y -
                                                  self.crane_starting_pos.y) * i
                                current_pos.z += (current_cmd[3].z -
                                                  self.crane_starting_pos.z) * i
                            case _:
                                ...
                    else:
                        self._inactive_simulation.set()

            rl.begin_drawing()
            rl.clear_background(rl.WHITE)
            rl.draw_text(f"fps: {rl.get_fps()}", 10, 10, 20, rl.GRAY)
            rl.begin_mode_3d(camera)

            self._draw_crane(current_pos)
            self._draw_containers()


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
            #print(f"{self.cmd_list[0][0]} @ t = {t} ms")
            match self.cmd_list[0][0]:
                case 'M':
                    self.crane_starting_pos = self.cmd_list[0][3]
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

    def _draw_containers(self):
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

    def _draw_crane(self, position: rl.Vector3):
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

    def exec(self, path: CranePath):
        """
        Execute a list of CraneCmd's supplied to append_cmds
        Raises:
            A ThreadError when the render thread (aka engine thread) has died
        """
        self._start_time = time.time_ns() // 1000_000
        with self.cmd_lock:
            self.cmd_list = path._cmds
        self._inactive_simulation.clear()
        self._inactive_simulation.wait()
        if not self._engine_is_running:
            raise threading.ThreadError("Engine thread stopped")

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
        self.containers.clear()
        if len(args) > self.plane.x - 1:
            raise ValueError("invalid x dimension (max x = "
                             f"{self.plane.x - 2})")

        for arg in args:
            if type(arg) != list:
                raise TypeError("not a list!")
            elif len(arg) > self.plane.z:
                raise ValueError("invalid z dimention (max z = "
                                 f"{self.plane.z - 3})")
            for a in arg:
                if a > (self.plane.y):
                    raise ValueError("invalid y dimention (max y = "
                                     f"{self.plane.y - 1})")
            self.containers.append(arg)
