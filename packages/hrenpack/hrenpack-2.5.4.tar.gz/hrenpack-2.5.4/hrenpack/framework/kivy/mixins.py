import platform
from logging import debug
from typing import Optional
from kivy.app import App
from kivy.core.image import Image as CoreImage
from kivy.core.window import Window
from kivy.graphics import Rectangle
from hrenpack.listwork import tuplist, key_in_dict
from hrenpack.filework.programming_language_work import KivyStylesFile


class WindowMixin:
    """При наследовании обязательно ставить перед классом App, иначе не сработает
    При использовании виджетов с динамическим размером, до изменения размеров окна размер виджета очень крупный"""
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


class WidgetMixin:
    def __init__(self, **kwargs):
        self._style: Optional[KivyStylesFile] = None
        if 'bind' in kwargs:
            self.bind(**kwargs['bind'])
            del kwargs['bind']
        if 'kvs_file' in kwargs:
            file = kwargs['kvs_file']
            if type(file) is KivyStylesFile:
                file.apply(self)
            elif type(file) is str:
                file = KivyStylesFile(file)
                file.apply(self)
            else:
                raise TypeError('kvs_file must be a KivyStylesFile object')

    def disable(self):
        self.disabled = True

    def enable(self):
        self.disabled = False

    @staticmethod
    def get_app():
        return App.get_running_app()


class LayoutMixin(WidgetMixin):
    def add_widgets(self, widgets: tuplist, *args, **kwargs):
        for widget in widgets:
            self.add_widget(widget, *args, **kwargs)

    def add(self, *widgets):
        self.add_widgets(widgets)

    def all_widgets(self):
        return self.children


class ImageBackgroundMixin:
    def __init__(self, **kwargs):
        with self.canvas.before:
            if key_in_dict(kwargs, 'bg_image'):
                self._bg_image = self._val(kwargs['bg_image'])
                del kwargs['bg_image']
            self._rect = Rectangle(size=self.size, pos=self.pos, texture=self._bg_image)
            self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self._rect.pos = instance.pos
        self._rect.size = instance.size

    @property
    def bg_image(self):
        return self._bg_image

    @bg_image.setter
    def bg_image(self, value):
        self._bg_image = self._val(value)
        self._rect.texture = self._bg_image

    @staticmethod
    def _val(value):
        if isinstance(value, CoreImage):
            bg_image = value.texture
        elif isinstance(value, str):
            bg_image = CoreImage(value).texture
        else:
            bg_image = value
        return bg_image
