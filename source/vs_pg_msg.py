"""
(c) Vitaly Smirnov [VSdev]
mrmaybelately@gmail.com
2024
"""

from enum import Enum

import pygame as pg


# classes list
class Align: ...
class Message: ...
class StaticMessage: ...


# It's not possible to use default font as a parameter without font.init() !?
pg.font.init()


class Align(Enum):
    LEFT: int = 0
    CENTER: int = 1
    RIGHT: int = 2


def get_align_x(align: Align, text_width: int, dest_width: int, 
                indent: int=0) -> int:
    match align:
        case Align.CENTER:
            return (dest_width - text_width) // 2
        case Align.LEFT:
            return indent
        case Align.RIGHT:
            return dest_width - text_width - indent


def render_text_board(  # Is this too much?
    msgs: tuple[str] | list[str],
    font: pg.font.Font=pg.font.Font(None, 25),
    text_align: Align=Align.CENTER,
    text_color: tuple[int, int, int]=(0, 0, 0),
    bg_color: tuple[int, int, int]=(255, 255, 255),
    frame_width: int=0,
    frame_color: tuple[int, int, int]=(0, 0, 0),
    vertical_indent: int=10,
    horizontal_indent: int=10,
    ) -> pg.surface.Surface:
    """ It returns a Surface (rect) with text on it """
    # Render the text and calculate a surface size
    images = list()
    width = 0
    height = vertical_indent
    for msg in msgs:
        image = font.render(msg, True, text_color, None)
        images.append(image)
        
        if image.get_width() > width:
            width = image.get_width()
        height += image.get_height() + vertical_indent
    width += horizontal_indent * 2

    # Create a surface
    text_board = pg.surface.Surface((width, height))
    text_board.fill(bg_color)

    # Draw a frame if needed
    if frame_width > 0:  # if frame_width == 0 draw.rect() will draw solid rect, so we should check it
        pg.draw.rect(text_board, frame_color, text_board.get_rect(), frame_width) # An alpha won't work

    # Draw the text images on result surface
    y = vertical_indent
    for image in images:
        x = get_align_x(text_align, image.get_width(), width, horizontal_indent)
        text_board.blit(image, (x, y))
        y += image.get_height() + vertical_indent

    return text_board


def is_key_down_in(event: pg.event.Event, keys: tuple | list) -> bool:
    return event.type == pg.KEYDOWN and event.key in keys


def is_key_down_esc_or_return(event: pg.event.Event) -> bool:
    return is_key_down_in(event, [pg.K_ESCAPE, pg.K_RETURN])


def get_is_key_down_in(keys: tuple | list): # -> function:
    def is_key_down_in(event: pg.event.Event) -> bool:
        return event.type == pg.KEYDOWN and event.key in keys
    return is_key_down_in


def wait_for_event(stop_condition, *args, **kwargs) -> pg.event.Event:
    while True:
        event = pg.event.wait()
        if stop_condition(event, *args, **kwargs):
            return event


def show_rendered_message(
    msg_surface: pg.Surface,
    screen: pg.surface.Surface,
    exit_condition=is_key_down_esc_or_return,
    pos: tuple[int, int] | None=None,  # if pos == None pos will be centred
    fit_into: bool=True
    ) -> pg.event.Event:
    """ It returns an occured event
        if pos is None pos will be centred
        (it won't work correct if pos is negative) """
    text_rect = msg_surface.get_rect() #.copy()  # It won't change

    was_scaled = fit_into and fit_rect(text_rect, screen.get_rect())
    if was_scaled:
        msg_surface = pg.transform.smoothscale(
            msg_surface, (text_rect.width, text_rect.height))
        text_rect = msg_surface.get_rect() #.copy()

    # This should be checked
    if pos == None:
        text_rect.center = screen.get_rect().center
    elif was_scaled:  # pos != None
        text_rect.topleft = pos #deepcopy(pos)
        if text_rect.right > screen.get_width():
            text_rect.centerx = screen.get_rect().centerx
        if text_rect.bottom > screen.get_height():
            text_rect.centery = screen.get_rect().centery
    else:  # pos != None and rect wasn't scaled!
        text_rect.topleft = pos
    screen.blit(msg_surface, text_rect) #.topleft)
    
    pg.display.flip()

    return wait_for_event(exit_condition)


def show_custom_message( # Is this too much?
    msgs: tuple[str] | list[str],
    screen: pg.surface.Surface,
    exit_condition=is_key_down_esc_or_return,
    pos: tuple[int, int] | None=None,  # if pos == None pos will be centred
    fit_into: bool=True,
    font: pg.font.Font=pg.font.Font(None, 25),
    text_align: Align=Align.CENTER,
    text_color: tuple[int, int, int]=(0, 0, 0),
    bg_color: tuple[int, int, int]=(255, 255, 255),
    frame_width: int=0,
    frame_color: tuple[int, int, int]=(0, 0, 0),
    alpha: int=255,
    vertical_indent: int=10,
    horizontal_indent: int=10
    ) -> pg.event.Event:
    """ It returns an occured event
        if pos is None pos will be centred
        (it won't work correct if pos is negative) """
    text_board = render_text_board(msgs, font, text_align, text_color, bg_color,
        frame_width, frame_color, vertical_indent, horizontal_indent)
    text_board.set_alpha(alpha)

    return show_rendered_message(text_board, screen, exit_condition, pos, fit_into)


def fit_rect(internal: pg.Rect, external: pg.Rect) -> bool:
    """ It returns True if internal rect has been changed """
    was_changed = False
    if internal.width > external.width:
        k = float(external.width) / float(internal.width)
        internal.width = external.width # int(float(text_rect.width) * k)
        internal.height = int(float(internal.height) * k)
        was_changed = True

    if internal.height > external.height:
        k = float(external.height) / float(internal.height)
        internal.height = external.height # int(float(text_rect.width) * k)
        internal.width = int(float(internal.width) * k)
        was_changed = True
    
    return was_changed


# It isn't used (do we need this?)
def draw_frame(surface: pg.surface.Surface, rect: tuple[int, int, int, int],
    color: tuple[int, int, int, (int)], width: int, radius: int=0) -> None:
    """ It draws frame with alpha """
    bg_surface = pg.surface.Surface((rect.width, rect.height))
    bg_surface.set_alpha(color[3])
    bg_surface.fill((255, 0, 255))
    bg_surface.set_colorkey((255, 0, 255))
    pg.draw.rect(bg_surface, color, bg_surface.get_rect(), width)
    #pg.draw.rect(surface, (100, 100, 100, 00), rect, 0) # An alpha won't work
    surface.blit(bg_surface, rect)


class Message:
    def __init__(self,
        msg: tuple[str] | list[str],
        screen: pg.Surface, 
        exit_condition=is_key_down_esc_or_return,
        pos: tuple[int, int] | None=None,
        fit_into: bool=True,
        font: pg.font.Font=pg.font.Font(None, 25),
        text_align: Align=Align.CENTER,
        text_color: tuple[int, int, int]=(0, 0, 0),
        bg_color: tuple[int, int, int]=(255, 255, 255),
        frame_width: int=0,
        frame_color: tuple[int, int, int]=(0, 0, 0),
        alpha: int=255,
        vertical_indent: int=10,
        horizontal_indent: int=10
        ) -> None:
        self.screen = screen
        self.exit_condition = exit_condition
        self.pos = pos
        self.fit_into = fit_into

        self._font = font
        self._text_align = text_align
        self._text_color = text_color
        self._bg_color = bg_color
        self._frame_width = frame_width
        self._frame_color = frame_color
        self._alpha = alpha
        self._vertical_indent = vertical_indent
        self._horizontal_indent = horizontal_indent
        
        # self._exit_condition = lambda event: (
        #     event.type == pg.KEYDOWN and event.key in self._exit_keys)
        
        self._render(msg)


    def _render(self, msg: tuple[str] | list[str]) -> pg.Surface:
        self._message_image = render_text_board(msg, self._font, self._text_align,
            self._text_color, self._bg_color, self._frame_width, self._frame_color,
            self._vertical_indent, self._horizontal_indent)
        self._message_image.set_alpha(self._alpha)


    def show(self, msg: tuple[str] | list[str] | None=None) -> pg.event.Event:
        """ If msg is None, it will show previous rendered message """
        if msg != None:
            self._render(msg)
        return show_rendered_message(self._message_image, self.screen,
            self.exit_condition, self.pos, self.fit_into)

    def __call__(self, msg: tuple[str] | list[str] | None=None) -> pg.event.Event:
        return self.show(msg)
    

class StaticMessage:
    """ It renders message once and then shows it as many times as needed
        without rerendering """
    def __init__(self, 
        msg: tuple[str] | list[str],
        screen: pg.Surface, 
        exit_condition=is_key_down_esc_or_return,
        pos: tuple[int, int] | None=None,
        fit_into: bool=True,
        font: pg.font.Font=pg.font.Font(None, 25),
        text_align: Align=Align.CENTER,
        text_color: tuple[int, int, int]=(0, 0, 0),
        bg_color: tuple[int, int, int]=(255, 255, 255),
        frame_width: int=0,
        frame_color: tuple[int, int, int]=(0, 0, 0),
        alpha: int=255,
        vertical_indent: int=10,
        horizontal_indent: int=10
        ) -> None:
        self.screen = screen
        self.exit_condition = exit_condition
        self.pos = pos
        self.fit_into = fit_into

        self._message_image = render_text_board(msg, font, text_align,
            text_color, bg_color, frame_width, frame_color,
            vertical_indent, horizontal_indent)
        self._message_image.set_alpha(alpha)


    def show(self) -> pg.event.Event:
        return show_rendered_message(self._message_image, self.screen,
            self.exit_condition, self.pos, self.fit_into)

    def __call__(self, msg: tuple[str] | list[str] | None=None) -> pg.event.Event:
        return self.show(msg)
