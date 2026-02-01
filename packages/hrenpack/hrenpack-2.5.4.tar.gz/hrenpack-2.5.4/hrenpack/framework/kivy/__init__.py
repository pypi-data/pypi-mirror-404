import platform
from logging import debug
from typing import Optional
from kivy.app import App as KivyApp
from kivy.core.window import Window


class App(KivyApp):
    width: int = 800
    height: int = 800
    title: str = "Window"
    pos_x: int = 0
    pos_y: int = 0
    resizable: bool = True
    fullscreen: bool = False
    borderless: bool = False
    min_width: int = 0
    min_height: int = 0
    max_width: int = 32767
    max_height: int = 32767
    alpha: float = 0
    icon: Optional[str] = None

    def on_start(self):
        if self.alpha < 0 or self.alpha > 1:
            raise ValueError('Alpha must be between 0 and 1')
        Window.title = self.title
        Window.resizable = self.resizable
        Window.fullscreen = self.fullscreen
        Window.borderless = self.borderless
        Window.min_width = self.min_width
        Window.min_height = self.min_height
        Window.max_width = self.max_width
        Window.max_height = self.max_height
        Window.alpha = self.alpha
        if platform.system() == 'Windows':
            Window.size = (self.width, self.height)
            Window.pos = (self.pos_x, self.pos_y)
        if self.icon:
            Window.icon = self.icon
        debug("WindowMixin initialized")


def pos_hint(x: Optional[float] = None, y: Optional[float] = None,
             center_x: Optional[float] = None, center_y: Optional[float] = None):
    output = {'x': x, 'y': y, 'center_x': center_x, 'center_y': center_y}
    for key in ('x', 'y', 'center_x', 'center_y'):
        if output[key] is None:
            del output[key]
        elif output[key] > 1:
            output[key] /= 100
    return output


def rgba(red: int, green: int, blue: int, alpha: int = 100):
    if red > 255:
        raise ValueError("Red value must be less than 255")
    elif red < 0:
        raise ValueError("Red value must be greater than 0")
    elif green > 255:
        raise ValueError("Green value must be less than 255")
    elif green < 0:
        raise ValueError("Green value must be greater than 0")
    elif blue > 255:
        raise ValueError("Blue value must be less than 255")
    elif blue < 0:
        raise ValueError("Blue value must be greater than 0")
    elif alpha > 100:
        raise ValueError("Alpha value must be less than 100")
    elif alpha < 0:
        raise ValueError("Alpha value must be greater than 0")
    else:
        return red / 255, green / 255, blue / 255, alpha / 100


def remove_parents(*widgets):
    for widget in widgets:
        widget.remove_parent()
