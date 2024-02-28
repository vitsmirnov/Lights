"""
(c) Vitaly Smirnov [VSdev]
mrmaybelately@gmail.com
2024
"""

import pygame as pg

from dataclasses import dataclass
from copy import deepcopy
from math import ceil
from functools import wraps

from vs_pg_msg import *  # It's ok, there are no conflicts
from lights_core import *  # It's ok, there are no conflicts
from settings_instance import SETTINGS_INSTANCE


# classes list
class UserInput: ...
class Sprites: ...
class GameSettings: ...
class LightsGame: ...


type Color = tuple[int, int, int]
type Size = tuple[int, int]


COLOR_FUCHSIA: Color = (255, 0, 255)
COLOR_FADED_YELLOW: Color = (255, 255, 128)
COLOR_DARK_YELLOW: Color = (255, 201, 14)
COLOR_DARK_BLUE: Color = (0, 0, 60)


@dataclass
class UserInput:
    event: int
    key: int

    def __hash__(self) -> int:
        return hash((self.event, self.key))

    def __eq__(self, other: UserInput) -> bool:
        return self.event == other.event and self.key == other.key

    def __ne__(self, other: UserInput) -> bool:
        return not self == other

    def __lt__(self, other: UserInput) -> bool:
        if self.event != other.event:
            return self.event < other.event
        return self.key < other.key

    def __gt__(self, other: UserInput) -> bool:
        if self.event != other.event:
            return self.event > other.event
        return self.key > other.key

    def __le__(self, other: UserInput) -> bool:
        return not self > other  # self < other or self == other

    def __ge__(self, other: UserInput) -> bool:
        return not self < other  # self > other or self == other


class Sprites:
    FORK_POS: Point = Point(0, 0)
    HOUSES_POS: Point = Point(4, 0)
    POWER_POS: Point = Point(5, 0)
    CURSOR_POS: Point = Point(5, 1)

    ERROR_MSG_CANT_LOAD = (
        "Error: can't load sprite images from: \"{}\". File not found.")
    
    def __init__(self, file_name: str, cell_width: int, cell_height: int, 
        transparent_color: pg.Color=COLOR_FUCHSIA, separator_width: int=0): 
        # separator_width - distance between sprites (in pixels)
        try:  # We can't run the game without this file
            image = pg.image.load(file_name).convert()
        except FileNotFoundError:
            print(self.ERROR_MSG_CANT_LOAD.format(file_name))
            raise FileNotFoundError(file_name)
        # image.set_colorkey(transparent_color)
        
        def get_rect(x: int, y: int) -> tuple[int, int, int, int]:
            x *= cell_width + separator_width
            y *= cell_height + separator_width
            return (x, y, x + cell_width, y + cell_height)
        
        def get_surface(p: Point) -> pg.Surface:
            result = pg.Surface((cell_width, cell_height)).convert()
            result.fill(transparent_color)
            result.set_colorkey(transparent_color)
            result.blit(image, (0, 0), get_rect(p.x, p.y))
            return result
        
        # creating forks
        self.forks = [[get_surface(self.FORK_POS.shifted(d.value, int(b)))
                       for b in [False, True]]
                       for d in Direction]
        # It could be a dictionary
        # self.forks = {d: {b: get_surface(self.FORK_POS.shifted(d.value, int(b)))
        #                   for b in [False, True]} for d in Direction}
        # creating houses
        self.houses = [get_surface(self.HOUSES_POS.shifted(0, int(b))) 
                       for b in [False, True]]
        # createing others
        self.power = get_surface(self.POWER_POS)
        self.cursor = get_surface(self.CURSOR_POS)


@dataclass
class GameSettings:  # class for default game settings. (Rename?) (AppSettings?)
    DEFAULT_RESOURCE_PATH = "..\\resource\\"  # temp
    
    sprites_file_name: str = DEFAULT_RESOURCE_PATH + "sprites.bmp"
    sprites_separator_width: int = 1
    sprites_transparent_color: Color = COLOR_FUCHSIA
    cell_size: Size = (50, 50)  # pixels
    cursor_alpha: int = 30  # 0..255
    background_file_name: str = DEFAULT_RESOURCE_PATH + "background.bmp"
    icon_file_name: str = DEFAULT_RESOURCE_PATH + "icon.bmp"
    icon_transparent_color: Color = COLOR_FUCHSIA
    show_cursor: bool = True
    message_text_color: Color = COLOR_DARK_YELLOW
    message_background_color: Color = COLOR_DARK_BLUE
    message_frame_color: Color = COLOR_DARK_YELLOW  # message_text_color
    message_alpha: int = 220  # 0..255
    message_font_size: int = 25
    message_frame_width: int = 1
    message_vert_indent: int = 10
    message_hor_indent: int = 10

    # level settings(?): field size, go through
    # controls?

    @staticmethod
    def load_from_file(file_name: str) -> GameSettings | None:
        """ It returns None if loading has failed and GameSettings object otherwise """
        result = GameSettings()
        try:
            with open(file_name, "r") as f:
                def readline() -> str:
                    f.readline()
                    return f.readline().strip()
                def readcolor() -> Color:
                    # colors should be checkd fo range (0..255)
                    r, g, b = readline().split()
                    return (int(r), int(g), int(b))
                def readint() -> int:
                    return int(readline())

                result.sprites_file_name = readline()
                result.sprites_separator_width = readint()  # *
                result.sprites_transparent_color = readcolor()  # *
                w, h = readline().split()
                result.cell_size = (int(w), int(h))  # *
                result.cursor_alpha = readint()  # *
                result.background_file_name = readline()
                result.icon_file_name = readline()
                result.icon_transparent_color = readcolor()  # *
                result.show_cursor = bool(readint())
                result.message_text_color = readcolor()  # *
                result.message_background_color = readcolor()  # *
                result.message_frame_color = readcolor()  # *
                result.message_alpha = readint()  # *
                result.message_font_size = readint()  # *
                result.message_frame_width = readint()  # *
                result.message_vert_indent = readint()  # *
                result.message_hor_indent = readint()  # *
                # * - these could be invalid and they should be checked for range!
        except:
            #print(f"Error: GameSettings.load_from_file({file_name}) failed.")
            return None
        else:
            return result


class LightsGame:
    SETTINGS_FILE_NAME = "settings.txt"
    SETTINGS_INSTANCE_FILE_NAME = "settings_instance.txt"
    DEFAULT_WINDOW_CAPTION = "Turn on the Lights"
    SCORE_CAPTION = ("Moves", "Score")  # "Moves" shows if net isn't united yet
    ICON_SIDE_LENGTH = 16
    CURSOR_ALPHA_STEP = 10
    CELL_SCALE_STEP = 2

    MSG_WELCOME = (
        "Hello!",
        "Press F1 for info")
        #"(esc to hide this message)")
    MSG_QUIT = ("Quit?", "enter/space - yes", "esc - no")
    MSG_HAS_WON = "The light is on!"
    MSG_YOUR_SCORE = "Your score: {}."
    MSG_PLAY_AGAIN = "Play again (enter/esc)?"  # (enter-space/esc)
    MSG_INFO = (
        "Controls:", #"Control keys:",
        " - turn left - left mouse button",
        " - turn right - right mouse button",
        " - new game - tab",
        " - change level - 1, 2, 3",
        # "Customize level:",
        " - change field size - W, S, A, D",
        " - go through on/off - ins",
        # "", #"Customize view:" #"Set up the view:",
        # " - + / - window size - + / - / ctrl+mouse wheel",
        # " - move window to center - home",
        " - show/hide cursor - del",
        " - info/about - F1",
        "",
        "About:",
        "   (c) Vitaly Smirnov. 2024", # [VSdev]
        "   mrmaybelately@gmail.com"
    )

    ERROR_MSG_CANT_LOAD_BACKGROUND = (
        "Error: can't load background image from: \"{}\". File not found.")
    ERROR_MSG_CANT_LOAD_ICON = (
        "Error: can't load icon image from: \"{}\". File not found.")


    # Public methods:

    def __init__(self, level_settings: LevelData=DEFAULT_LEVELS[0]):
        pg.init()  # pygame setup

        self._engine = Engine(level_settings)
        self._init_controls()
        settings = self._init_settings()
        self._init_screen(settings.background_file_name)  # background is initialized here
        # Crucial init here. If we can't load sprites, then we can't run the game
        self._init_sprites(settings.sprites_file_name,
            settings.sprites_transparent_color, settings.sprites_separator_width,
            settings.cursor_alpha)
        self._init_icons(settings.icon_file_name, settings.icon_transparent_color)
        self._set_icon()
        self._init_messages(self._message_font_size, self._message_frame_width,
            self._message_vert_indent, self._message_hor_indent)
        self._clock = pg.time.Clock()

    def run(self) -> None:
        self._update_screen()
        self._show_welcome_message()
        self._run_game_loop()
        pg.quit()

    def quit(self) -> None:
        if self._quit_msg.show().key != pg.K_ESCAPE:
            pg.event.post(pg.event.Event(pg.USEREVENT, {"code": 0})) #pg.event.Event(pg.QUIT))
    
    def turn_fork_left(self, pos: tuple[int, int]) -> None:
        x, y = pos #pg.mouse.get_pos()
        self._engine.turn_left((x // self._cell_width, y // self._cell_height))
    
    def turn_fork_right(self, pos: tuple[int, int]) -> None:
        x, y = pos #pg.mouse.get_pos()
        self._engine.turn_right((x // self._cell_width, y // self._cell_height))

    @staticmethod
    def _screen_size_updater(func):# -> function:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            self._update_screen_size()
            return result  # Just in case (it isn't used in this case )
        return wrapper

    @_screen_size_updater
    def set_level1(self) -> None:
        self._engine.set_level(DEFAULT_LEVELS[0])
    
    @_screen_size_updater
    def set_level2(self) -> None:
        self._engine.set_level(DEFAULT_LEVELS[1])
    
    @_screen_size_updater
    def set_level3(self) -> None:
        self._engine.set_level(DEFAULT_LEVELS[2])
    
    @_screen_size_updater
    def inc_width(self) -> None:
        self._engine.field_width += 1
    
    @_screen_size_updater
    def dec_width(self) -> None:
        self._engine.field_width -= 1
    
    @_screen_size_updater
    def inc_height(self) -> None:
        self._engine.field_height += 1
    
    @_screen_size_updater
    def dec_height(self) -> None:
        self._engine.field_height -= 1
    
    def switch_go_through(self) -> None:
        self._engine.go_through = not self._engine.go_through
    
    def switch_cursor(self) -> None:
        self._show_cursor = not self._show_cursor
    
    def show_info(self) -> None:
        self._info_msg.show()

    def inc_cursor_alpha(self) -> None:
        cur_alpha = self._sprites.cursor.get_alpha()
        if cur_alpha != None and cur_alpha + self.CURSOR_ALPHA_STEP <= 255:  # it isn't magic number)
            self._sprites.cursor.set_alpha(cur_alpha + self.CURSOR_ALPHA_STEP)
    
    def dec_cursor_alpha(self) -> None:
        cur_alpha = self._sprites.cursor.get_alpha()
        if cur_alpha != None and cur_alpha - self.CURSOR_ALPHA_STEP >= 0:
            self._sprites.cursor.set_alpha(cur_alpha - self.CURSOR_ALPHA_STEP)

    def get_settings_instance(self) -> bool:
        """ It (will) create a file with settings example
            in the same directory as the main file
            It return True if successful """
        try:
            with open(self.SETTINGS_INSTANCE_FILE_NAME, "w") as f:
                f.writelines(SETTINGS_INSTANCE)  # use just write?
        except:
            print(f"Can't write to file \"{self.SETTINGS_INSTANCE_FILE_NAME}\".")
            return False
        return True
    
    # Experimental
    def inc_cell_size(self) -> None:
        self._scale_field(self.CELL_SCALE_STEP)
    
    # Experimental
    def dec_cell_size(self) -> None:
        self._scale_field(-self.CELL_SCALE_STEP)

    # For debugging (temp)
    def _finish_game(self):
        self._engine._net = deepcopy(self._engine._net_clone)
        #self._engine._update_net()

    # For debugging (temp)
    def _disassemble_lvl(self) -> None:
        self._engine._net.disassemble()
        self._engine._net.update(self._engine._power_pos, self._engine._go_through)

    @property
    def screen_size(self) -> tuple[int, int]:
        return (self._engine.field_width * self._cell_width,
                self._engine.field_height * self._cell_height)


    # Private methods:

    def _init_controls(self) -> None:
        def set_command(event: int, key: int, func) -> None:
            self._commands[UserInput(event, key)] = func
        def set_keydown_command(key: int, func) -> None:
            set_command(pg.KEYDOWN, key, func)
        
        self._commands = dict()
        set_keydown_command(pg.K_ESCAPE, self.quit)
        set_command(pg.WINDOWCLOSE, 0, self.quit)
        set_command(pg.MOUSEBUTTONUP, pg.BUTTON_LEFT, self.turn_fork_left)
        set_command(pg.MOUSEBUTTONUP, pg.BUTTON_RIGHT, self.turn_fork_right)
        set_keydown_command(pg.K_TAB, self._engine.new_game)
        set_keydown_command(pg.K_1, self.set_level1)
        set_keydown_command(pg.K_2, self.set_level2)
        set_keydown_command(pg.K_3, self.set_level3)
        set_keydown_command(pg.K_d, self.inc_width) #K_RIGHT
        set_keydown_command(pg.K_a, self.dec_width) #K_LEFT
        set_keydown_command(pg.K_s, self.inc_height) #K_DOWN
        set_keydown_command(pg.K_w, self.dec_height) #K_UP
        set_keydown_command(pg.K_INSERT, self.switch_go_through)
        set_keydown_command(pg.K_DELETE, self.switch_cursor)
        set_keydown_command(pg.K_F1, self.show_info)
        set_keydown_command(pg.K_KP_PLUS, self.inc_cursor_alpha)
        set_keydown_command(pg.K_KP_MINUS, self.dec_cursor_alpha)
        set_keydown_command(pg.K_h, self.get_settings_instance)
        # Experimental
        set_keydown_command(pg.K_0, self.inc_cell_size)
        set_keydown_command(pg.K_9, self.dec_cell_size)
        # For debugging (temp)
        set_keydown_command(pg.K_END, self._finish_game)
        set_keydown_command(pg.K_BACKSPACE, self._disassemble_lvl)

    def _init_settings(self) -> GameSettings:
        settings = GameSettings.load_from_file(self.SETTINGS_FILE_NAME)
        if settings == None:
            settings = GameSettings()

        # It's not good
        self._cell_width, self._cell_height = settings.cell_size
        self._show_cursor = settings.show_cursor
        self._message_text_color = settings.message_text_color
        self._message_background_color = settings.message_background_color
        self._message_frame_color = settings.message_frame_color
        self._message_alpha = settings.message_alpha
        self._message_font_size = settings.message_font_size
        self._message_frame_width = settings.message_frame_width
        self._message_vert_indent = settings.message_vert_indent
        self._message_hor_indent = settings.message_hor_indent

        return settings

    def _init_screen(self, file_name: str) -> None:
        # init background and set_display_mode
        # after this window will be shown
        # If we can't load a background image, we still can run the game
        try:
            self._background_image = pg.image.load(file_name)
        except FileNotFoundError:
            print(self.ERROR_MSG_CANT_LOAD_BACKGROUND.format(file_name))
            self._background_image = pg.surface.Surface(
                (self._cell_width, self._cell_height))
        self._update_screen_size()
        self._background_image = self._background_image.convert()
        pg.display.set_caption(self.DEFAULT_WINDOW_CAPTION)

    def _init_sprites(self, file_name: str, transparent_color: Color,
        separator_width: int, cursor_alpha: int) -> None:
        # init strites
        # we should init sprites after set_display_mode becaus of strite convertion
        # If we can't load sprites, we can't run the game
        self._sprites = Sprites(file_name, self._cell_width, self._cell_height,
            transparent_color, separator_width)
        self._sprites.cursor.set_alpha(cursor_alpha)

        # Experimental! (for inc/dec window size)
        # self._sprites_source = deepcopy(self._sprites) # It won't work
        self._sprites_source = Sprites(file_name, self._cell_width, self._cell_height,
            transparent_color, separator_width)
        self._sprites_source.cursor.set_alpha(cursor_alpha)

    def _init_icons(self, file_name: str,
        transparent_color: pg.Color | None=None) -> None:
        # init icons (plugged/unplugged)
        # If we can't load icons, we still can run the game
        try:
            icon_img = pg.image.load(file_name).convert()
        except FileNotFoundError: # We can run the game without icons
            self._icons = None
            print(self.ERROR_MSG_CANT_LOAD_ICON.format(file_name))
            return

        self._icons = list()
        side_len = self.ICON_SIDE_LENGTH
        for plugged in (False, True):
            icon = pg.surface.Surface((side_len, side_len))
            x = side_len * plugged
            icon.blit(icon_img, (0, 0), (x, 0, x + side_len, side_len))
            if transparent_color != None:
                icon.set_colorkey(transparent_color)
            self._icons.append(icon)
        self._current_icon_state = not self._engine.is_net_united

    def _init_messages(self, font_size: int=25, frame_width: int=3,
        frame_vert_indent: int=10, frame_hor_indent: int=10) -> None:
        cond = get_is_key_down_in((pg.K_ESCAPE, pg.K_RETURN, pg.K_SPACE))

        # To do: it should be refactored!
        self._quit_msg = StaticMessage(self.MSG_QUIT, self._screen, cond,
            None, True, pg.font.Font(None, font_size), Align.CENTER,
            self._message_text_color, self._message_background_color, frame_width,
            self._message_frame_color, self._message_alpha,
            frame_vert_indent, frame_hor_indent)
        self._game_over_msg = Message(self.MSG_HAS_WON, self._screen, cond,
            None, True, pg.font.Font(None, font_size), Align.CENTER,
            self._message_text_color, self._message_background_color, frame_width,
            self._message_frame_color, self._message_alpha,
            frame_vert_indent, frame_hor_indent)
        self._info_msg = StaticMessage(self.MSG_INFO, self._screen, cond,
            None, True, pg.font.Font(None, font_size), Align.LEFT,
            self._message_text_color, self._message_background_color, frame_width,
            self._message_frame_color, self._message_alpha,
            frame_vert_indent, frame_hor_indent)

    def _run_game_loop(self) -> None:
        while True:
            # _process_input() returns False if user wants to quit
            if not self._process_input():
                break
            
            self._update_logic()
            
            self._update_screen()

            self._clock.tick(60)  # limits FPS to 60 # dt = clock.tick(60) / 1000


    def _update_screen_size(self) -> None:  # Rename this?
        screen_size = self.screen_size

        self._background = pg.Surface(screen_size)
        fill_surface(self._background, self._background_image)
        
        self._screen = pg.display.set_mode(screen_size)
        self._background = self._background.convert()  # Is it useful?

    def _set_icon(self) -> None:
        if self._icons != None and self._current_icon_state != self._engine.is_net_united:
            self._current_icon_state = not self._current_icon_state
            pg.display.set_icon(self._icons[self._current_icon_state])

    def _process_input(self) -> bool:
        """ It returns False if game loop has to be broken (event.type == USEREVENT) """
        # poll for events
        for event in pg.event.get():
            #print(event)
            if event.type == pg.USEREVENT: #pg.QUIT:
                return False
            self._handle_input(event)
        return True

    def _update_logic(self) -> None:
        # Game over
        if self._engine.is_net_united:
            # print("Net is united!")
            self._update_screen()
            answer = self._game_over_msg.show(self._get_game_over_msg())
            if answer.key == pg.K_ESCAPE:
                pg.event.post(pg.event.Event(pg.USEREVENT, {"code": 0})) #pg.QUIT
            else:
                self._engine.new_game()

    def _update_screen(self) -> None:
        # Draw background
        self._screen.blit(self._background, (0, 0))
        
        # Draw net/field
        self._draw_net()
        
        # Draw cursor
        self._draw_cursor()

        # Show score/moves
        pg.display.set_caption(
            f"{self.SCORE_CAPTION[self._engine.is_net_united]}: {self._engine.score}")

        # Set/update icon
        self._set_icon()  # Icon will be reset only if needed

        # flip() the display to put your work on screen
        pg.display.flip()
        #pg.display.update() # ?


    def _handle_input(self, event: pg.event.Event) -> None:
        # 1. Translate input and prepare extra data (if needed)
        input = UserInput(event.type, 0)
        data = list()
        match event.type:
            case pg.KEYDOWN | pg.KEYUP:
                input.key = event.key
            case pg.MOUSEBUTTONDOWN | pg.MOUSEBUTTONUP:
                input.key = event.button
                data.append(event.pos)
            case pg.MOUSEMOTION:
                pass  # move cursor here
            case pg.MOUSEWHEEL:
                pass

        # 2. Do the command
        self._do_command(input, *data)

    def _do_command(self, input: UserInput, *args) -> None:
        command = self._commands.get(input)
        if command != None:
            command(*args)

    def _get_game_over_msg(self) -> tuple[str]:
        return (
            self.MSG_HAS_WON,
            self.MSG_YOUR_SCORE.format(self._engine.score),
            self.MSG_PLAY_AGAIN
        )

    def _show_welcome_message(self) -> None:
        cond = get_is_key_down_in((pg.K_F1, pg.K_ESCAPE, pg.K_RETURN, pg.K_SPACE))
        answer = show_custom_message(self.MSG_WELCOME, self._screen, cond,#msg_exit_cond,
            None, True, pg.font.Font(None, self._message_font_size), Align.CENTER,
            self._message_text_color, self._message_background_color,
            self._message_frame_width, self._message_frame_color, self._message_alpha,
            self._message_vert_indent, self._message_hor_indent)
        if answer.key == pg.K_F1:
            pg.event.post(pg.event.Event(pg.KEYDOWN, {"key": pg.K_F1}))


    def _draw_cell(self, x: int, y: int):
        # There is no need to do range check
        pos = (x * self._cell_width, y * self._cell_height)
        cell = self._engine.field(x, y)
        # Draw fork
        for dir in cell.fork:
            self._screen.blit(self._sprites.forks[dir.value][cell.is_plugged], pos)
        # Draw power
        if Point(x, y) == self._engine._power_pos:
            self._screen.blit(self._sprites.power, pos)
        # Draw house
        elif cell.fork.count == 1:
            self._screen.blit(self._sprites.houses[cell.is_plugged], pos)
        # Draw cursor ..

    def _draw_net(self):
        self._engine.field.for_each_index(lambda x, y: self._draw_cell(x, y))

    def _draw_cursor(self) -> None:
        if self._show_cursor and not self._engine.is_net_united:
            x, y = pg.mouse.get_pos()
            self._screen.blit(self._sprites.cursor, (
                (x // self._cell_width) * self._cell_width,
                (y // self._cell_height) * self._cell_height))

    # Experimental
    def _scale_field(self, scale_step: int=2) -> None:
        def is_valid(size: int) -> bool:
            return 30 <= (size + scale_step) <= 200
        if not is_valid(self._cell_width) or not is_valid(self._cell_height):
            return
        self._cell_width += scale_step
        self._cell_height += scale_step
        self._update_screen_size()
        self._scale_sprites()

    # Experimental
    def _scale_sprites(self) -> None:
        size = (self._cell_width, self._cell_height)
        # Forks
        for d in Direction: #.value:
            for b in (False, True):
                self._sprites.forks[d.value][b] = pg.transform.scale(
                    self._sprites_source.forks[d.value][b], size)
        # Houses
        for b in (False, True):
            self._sprites.houses[b] = pg.transform.scale(
                self._sprites_source.houses[b], size)
        # Others
        self._sprites.power = pg.transform.scale(self._sprites_source.power, size)
        self._sprites.cursor = pg.transform.scale(self._sprites_source.cursor, size)



""" functions """


def fill_surface(source: pg.surface.Surface,
    background: pg.surface.Surface) -> None:
    bg_width, bg_height = background.get_size()
    width = ceil(source.get_width() / bg_width)
    height = ceil(source.get_height() / bg_height)
    for j in range(height):
        for i in range(width):
            source.blit(background, (i * bg_width, j * bg_height))


"""
keys_state = set()  # pressed (held) keys

def keys_state_monitoring(get_event_func):#: function) -> function:
    def wrapper(*args, **kwargs):
        events = get_event_func(*args, **kwargs)
        for event in events:
            match event.type:
                case pg.KEYDOWN:
                    keys_state.add(event.key)
                case pg.MOUSEBUTTONDOWN:
                    keys_state.add(event.button)
                case pg.KEYUP:
                    keys_state.discard(event.key)
                case pg.MOUSEBUTTONUP:
                    keys_state.discard(event.button)
        #pg.display.set_caption(str(keys_state))
        #print(keys_state)
        return events
    return wrapper

pg.event.get = keys_state_monitoring(pg.event.get)
#"""
