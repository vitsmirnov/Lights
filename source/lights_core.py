"""
(c) Vitaly Smirnov [VSdev]
mrmaybelately@gmail.com
https://github.com/vitsmirnov
2024
"""

from enum import Enum
from random import randint, choice
from copy import deepcopy
from dataclasses import dataclass, field
from functools import singledispatchmethod


# classes list
class Point: ...
class Direction: ...
class Fork: ...
class Cell: ...
class Net: ...
class LevelData: ...
class Engine: ...


# classes

@dataclass
class Point:
    x: int = 0
    y: int = 0

    def setup(self, x: int, y: int) -> None:
        self.x, self.y = x, y
    
    def assign(self, pos: tuple[int, int]) -> None:
        self.x, self.y = pos
    
    def copy_from(self, other: Point) -> None:
        self.setup(other.x, other.y)

    @property  # it isn't property!
    def as_tuple(self) -> tuple[int, int]:
        return (self.x, self.y)
    
    def shifted(self, x: int, y: int) -> Point:
        return Point(self.x + x, self.y + y)
    
    def clone(self) -> Point:
        return deepcopy(self)


class Direction(Enum):  # Should it be IntEnum?
    DIR0 = 0
    DIR90 = 1
    DIR180 = 2
    DIR270 = 3

    def __int__(self) -> Direction:
        return self.value

    def __neg__(self) -> Direction:
        return Direction.DIR0.turned(-self.value)
    
    def __str__(self) -> str:
        return self.name

    def turned(self, dir: int | Direction) -> Direction:
        return Direction((self.value + int(dir)) % len(Direction))

    @property  # It probably shouldn't be a property
    def next(self) -> Direction:
        return self.turned(1)
    
    @property
    def prev(self) -> Direction:
        return self.turned(-1)

    @property
    def opposite(self) -> Direction:
        return self.turned(self.DIR180)
    
    def is_opposite(self, other: Direction) -> bool:
        return self == other.opposite


class Fork:
    def __init__(self, *directions: Direction | int):
        self._fork = set()  # Rename to "_directions"?
        # an alternative implementation of fork data could be
        # self._fork = [False for _ in range(len(Directions))]
        self.add(*directions)

    def __contains__(self, item: Direction) -> bool:
        return item in self._fork
    
    def __iter__(self): # -> Iterator:
        return self._fork.__iter__()

    def add(self, *directions: Direction | int) -> None:
        for dir in directions:
            self._fork.add(Direction(dir))

    def remove(self, *directions: Direction | int) -> None:
        for dir in directions:
            self._fork.discard(Direction(dir))

    def clear(self) -> Fork:
        self._fork.clear()
        return self

    def fill(self) -> None:
        # self._fork = set(d for d in Direction) # Is it effective?
        for d in Direction:
            self._fork.add(d)

    @property
    def count(self) -> int:
        return len(self._fork)
    
    def turned(self, dir: int) -> set:
        result = set()
        for f in self._fork:
            result.add(f.turned(dir))
        return result
    
    def turn(self, dir: int) -> None:
        self._fork = self.turned(dir)  # Is it effective?
    
    def turn_right(self) -> None:
        self.turn(1)

    def turn_left(self) -> None:
        self.turn(-1)
    
    @property
    def is_straight(self) -> bool:
        #return self.count == 2 and self._fork[0] == self._fork[1].opposite
        if self.count == 2:
            first, second = self._fork # tuple(self._fork)
            return first == second.opposite

    @property
    def is_full(self) -> bool:
        return self.count == len(Direction)
    
    @property
    def is_empty(self) -> bool:
        return self.count == 0


@dataclass
class Cell:
    fork: Fork = field(default_factory=Fork)
    is_plugged: bool = False
    
    def setup(self, fork: Fork, is_plugged: bool) -> None:
        self.fork, self.is_plugged = fork, is_plugged

    def copy_from(self, other: Cell) -> None:
        self.setup(deepcopy(other.fork), other.is_plugged)
    
    def __contains__(self, item: Direction) -> bool:
        return item in self.fork


class Net:
    MIN_WIDTH: int = 2
    MIN_HEIGHT: int = 2
    MAX_WIDTH: int = 100
    MAX_HEIGHT: int = 100
    DEFAULT_WIDTH: int = 5
    DEFAULT_HEIGHT: int = 4

    def __init__(self, width: int=DEFAULT_WIDTH, height: int=DEFAULT_HEIGHT,
                 cell: Cell=Cell()):
        # Cell() as a default parameter is safe here, because it's copied (deep)
        self._cells = list()
        self.setup(width, height, cell)

    def setup(self, width: int, height: int, cell: Cell=Cell()) -> bool:
        """ It returns True if size was changed nad False otherwise """
        # Cell() as a default parameter is safe here, because it's copied (deep)
        width, height = self._fitted_size((width, height))
        if self.width == width and self.height == height:
            return False
        self._setup(width, height, cell)
        return True

    def reset(self, fork: Fork=Fork(), is_plugged: bool=False) -> None:
        # Fork() as a default parameter is safe here, because it's copied (deep)
        self.for_each(lambda cell: cell.setup(deepcopy(fork), is_plugged))


    def generate(self, go_through: bool) -> bool:  # rename to create?
        """ It return True if the maze is united (and was successfully generated) """
        start_pos = Point(randint(0, self.width-1), randint(0, self.height-1))
        return self._traversal(start_pos, go_through, True) == self.area

    def update(self, start_pos: Point, go_through: bool) -> bool:
        """ It returns True if the net is united and False otherwise """
        return self._traversal(start_pos, go_through, False) == self.area # - skiped_cells_count

    def disassemble(self) -> tuple[int, int]:
        """ it returns a number of cells which could be turned (not empty or full) and
            a minimal number of steps (/clicks), that needed to assemble the net """
        turned_cells_count = 0
        back_steps_count = 0

        for col in self._cells:
            for cell in col:
                #if not cell.fork.is_empty and not cell.fork.is_full:
                if 0 < cell.fork.count < len(Direction):
                    turned_cells_count += 1
                    turn = randint(0, len(Direction)-1)
                    cell.fork.turn(turn)
                    back_steps_count += turn
        
                    # fix back_steps_count (in these cases it doesn't equal to forward turn)
                    if turn == Direction.DIR270.value:
                        back_steps_count -= 2
                    elif turn == Direction.DIR180.value and cell.fork.is_straight:
                        back_steps_count -= 2

        return (turned_cells_count, back_steps_count)

    def disassemble2(self) -> None:
        self.for_each(lambda cell: cell.fork.turn(randint(0, len(Direction)-1)))

    @property
    def is_united(self) -> bool:
        for col in self._cells:
            for cell in col:
                if not cell.is_plugged and not cell.fork.is_empty:
                    return False
        return True


    @property
    def width(self) -> int:
        return len(self._cells)

    @width.setter
    def width(self, value: int) -> None:
        value = self._fitted_width(value)
        if self.width != value:
            self._setup(value, self.height)

    @property
    def height(self) -> int:
        return len(self._cells[0]) if self.width > 0 else 0

    @height.setter
    def height(self, value: int) -> None:
        value = self._fitted_height(value)
        if self.height != value:
            self._setup(self.width, value)

    @property
    def size(self) -> tuple[int, int]:
        return self.width, self.height
    
    @size.setter
    def size(self, value: tuple[int, int]) -> None:
        w, h = value
        self.setup(w, h)

    @property
    def area(self) -> int:
        return self.width * self.height

    def __getitem__(self, key: Point) -> Cell:  # Do it for tuple (as key) too?
        return self._cells[key.x][key.y] #[x][y]

    # Do we need this?
    def __setitem__(self, key: Point, value: Cell) -> None: # | tuple[int, int]
        self._cells[key.x][key.y] = value

    # It's doubtful
    def __call__(self, x: int, y: int) -> Cell:
        """ It works like an indexing [index], but for two coordinates,
            so it returns Cell(x, y). Note, that it DOESN'T do range checks! """
        return self._cells[x][y]

    def get_at(self, pos: Point) -> Cell:
        if self.does_pos_exist(pos):
            return self._cells[pos.x][pos.y]
        #raise IndexError()

    def set_at(self, pos: Point, cell: Cell) -> None:
        if self.does_pos_exist(pos):
            self._cells[pos.x][pos.y] = cell


    def does_pos_exist(self, pos: Point) -> bool:
        return self.does_pos_exist_xy(pos.x, pos.y)
    
    def does_pos_exist_xy(self, x: int, y: int) -> bool:
        return (0 <= x < self.width) and (0 <= y < self.height)

    def for_each(self, func, *args, **kwargs) -> None:
        for col in self._cells:
            for cell in col:
                func(cell, *args, **kwargs)

    def for_each_index(self, func, *args, **kwargs) -> None:
        width = self.width
        height = self.height
        for i in range(height):
            for j in range(width):
                func(j, i, *args, **kwargs)


    def _setup(self, width: int, height: int, cell: Cell=Cell()) -> None:
        self._cells.clear()  # do we need this? Or this: del self._cells ?
        # Well, I guess clear() could help for garbage collector, but I'm not sure
        self._cells = [[deepcopy(cell)
                        for _ in range(height)]
                        for _ in range(width)] # is it effective?

    def _traversal(self, start_pos: Point, go_through: bool,
        creation_mode: bool=False) -> int: # cells_to_skip: list[Point]
        """ It returns a number of visited/plugged cells """
        if not self.does_pos_exist(start_pos):
            return 0 # -1?
        
        def has_connection(cur_pos: Point, next_pos: Point, dir: Direction) -> bool:
            return (dir in self[cur_pos].fork) and (dir.opposite in self[next_pos].fork)

        def get_next_pos(pos: Point, dir: Direction) -> Point:
            np = next_pos(pos, dir)
            if go_through and not self.does_pos_exist(np):
                return Point(np.x % self.width, np.y % self.height)
            return np
        
        # reset the net
        self.for_each(lambda cell: cell.setup(
            cell.fork.clear() if creation_mode else cell.fork, False))

        pos = start_pos.clone() # deepcopy(start_pos)  # just in case
        self[pos].is_plugged = True
        plugged_count = 1

        path = list()
        unvisited = list() # set?
        while True:
            unvisited.clear()

            for dir in Direction:
                np = get_next_pos(pos, dir)
                if self.does_pos_exist(np) and not self[np].is_plugged and (
                    creation_mode or has_connection(pos, np, dir)):
                    unvisited.append(dir)
                    if not creation_mode:
                        break

            if len(unvisited) > 0:
                dir = choice(unvisited)
                if creation_mode:
                    self[pos].fork.add(dir)
                path.append(pos) # deepcopy isn't needed
                pos = get_next_pos(pos, dir)
                if creation_mode:
                    self[pos].fork.add(dir.opposite)
                self[pos].is_plugged = True
                plugged_count += 1
            else:
                if len(path) == 0:
                    break
                pos = path.pop()
        
        return plugged_count

    def _fitted_width(self, width: int) -> int:
        return fit_into(width, self.MIN_WIDTH, self.MAX_WIDTH)
    
    def _fitted_height(self, height: int) -> int:
        return fit_into(height, self.MIN_HEIGHT, self.MAX_HEIGHT)

    def _fitted_size(self, size: tuple[int, int]) -> tuple[int, int]:
        w, h = size
        return (self._fitted_width(w), self._fitted_height(h))


@dataclass
class LevelData:
    field_size: tuple[int, int] = (Net.DEFAULT_WIDTH, Net.DEFAULT_HEIGHT) 
    go_through: bool = False


class Engine:
    SCORE_GO_THROUGH_COEFF = 4
    POINTS_PER_CELL = 10  # Amount of points per cell (if it isn't empty)

    def __init__(self, settings: LevelData=LevelData()):
        # We don't change settings, so it's safe to use LevelData()
        # as a default parameter
        w, h = settings.field_size
        self._net = Net(w, h, Cell())
        self._go_through = settings.go_through

        self._power_pos = Point((self._net.width-1) // 2, (self._net.height-1) // 2)
        
        self._is_net_united = False
        self._turned_cells_count = 0
        self._back_steps_count = 0
        self._moves_count = 0

        self.new_game()

    def set_settings(self, field_size: tuple[int, int], go_through: bool) -> None:
        field_size_changed = self._set_field_size(field_size, False)
        go_through_changed = self._set_go_through(go_through, False)
        if field_size_changed or go_through_changed:        
            self.new_game()

    def set_level(self, level: LevelData) -> None:
        self.set_settings(level.field_size, level.go_through)

    @property
    def field_size(self) -> tuple[int, int]:
        return self._net.size

    @field_size.setter
    def field_size(self, value: tuple[int, int]) -> None:
        self._set_field_size(value, True)

    @property
    def field_width(self) -> int:
        return self._net.width
    
    @field_width.setter
    def field_width(self, value: int) -> None:
        self._set_field_size((value, self.field_height), True)

    @property
    def field_height(self) -> int:
        return self._net.height
    
    @field_height.setter
    def field_height(self, value: int) -> None:
        self._set_field_size((self.field_width, value), True)

    @property
    def go_through(self) -> bool:
        return self._go_through
    
    @go_through.setter
    def go_through(self, value: bool) -> None:
        self._set_go_through(value, True)


    def new_game(self) -> None:
        self._is_net_united = self._net.generate(self._go_through)
        self._net_clone = deepcopy(self._net) # For debugging (temp)
        while self._is_net_united:  # this should be done only once in most cases (just in case)
            self._turned_cells_count, self._back_steps_count = self._net.disassemble()
            self._update_net()
        self._moves_count = 0

    @singledispatchmethod
    def turn_right(self, pos: Point) -> None:
        self._turn(pos, lambda p: self._net[p].fork.turn_right())
    
    @singledispatchmethod
    def turn_left(self, pos: Point) -> None:
        self._turn(pos, lambda p: self._net[p].fork.turn_left())
    
    @turn_right.register(tuple) # [int, int]
    def _(self, pos: tuple[int, int]) -> None:
        self.turn_right(Point(pos[0], pos[1]))  # Is it ok (indexing)?
    
    @turn_left.register(tuple) # [int, int]
    def _(self, pos: tuple[int, int]) -> None:
        self.turn_left(Point(pos[0], pos[1]))  # Is it ok (indexing)?

    @property
    def is_net_united(self) -> bool:  # rename to state?
        #return self._net.update(self._power_pos, self._go_through)
        return self._is_net_united  # self._net.is_united

    @property
    def score(self) -> int:
        if self.is_net_united:
            return self._calc_score() - self.moves_count
        else:
            return self.moves_count

    @property
    def moves_count(self) -> int:  # It isn't used
        return self._moves_count

    @property
    def field(self) -> Net:
        return self._net


    def _set_field_size(self, value: tuple[int, int], start_new_game: bool) -> bool:
        """ It returns True if size was changed and False otherwise """
        w, h = value
        result = self._net.setup(w, h, Cell())
        if result:
            self._power_pos = Point((self.field_width-1) // 2, (self.field_height-1) // 2)
            if start_new_game:
                self.new_game()
        return result

    def _set_go_through(self, value: bool, start_new_game: bool) -> bool:
        """ It returns True if go_through was changed and False otherwise """
        if self.go_through == value:
            return False
        self._go_through = value
        if start_new_game:
            self.new_game()
        return True

    def _turn(self, pos: Point, turn_func) -> None:  # It could be a decorator (?)
        if not self._net.does_pos_exist(pos) or self.is_net_united:
            return
        turn_func(pos)
        self._moves_count += 1
        self._update_net()

    def _update_net(self) -> bool:
        """ It returns True if the net is united and False otherwise """
        self._is_net_united = self._net.update(self._power_pos, self._go_through)
        return self._is_net_united

    def _calc_score(self) -> int:
        k = self.SCORE_GO_THROUGH_COEFF if self._go_through else 1
        return self._turned_cells_count * self.POINTS_PER_CELL * k + (
            self._back_steps_count)



DEFAULT_LEVELS = (
    LevelData((5, 4), False),
    LevelData((9, 9), False),
    LevelData((9, 9), True)
)


""" functions """

def next_pos(pos: Point, dir: Direction) -> Point:
    match dir:
        case Direction.DIR0:
            return pos.shifted(0, -1) #return Point(pos.x, pos.y - 1) 
        case Direction.DIR90:
            return pos.shifted(1, 0)
        case Direction.DIR180:
            return pos.shifted(0, 1)
        case Direction.DIR270:
            return pos.shifted(-1, 0)

def tuple_to_point(t: tuple[int, int]) -> Point:
    if isinstance(t, tuple[int, int]): # and len(t) >= 2 and type(t[0]) is int and type(t[1]) is int:
        return Point(t[0], t[1])
    return t

def fit_into(value: int, min: int, max: int) -> int:
    if min <= value <= max:
        return value
    elif value > max:
        return max
    else:  # if value < min (or max < min)
        return min
