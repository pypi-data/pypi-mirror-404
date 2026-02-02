from abc import ABC, ABCMeta, abstractmethod
from typing import Literal
from kivy.uix.widget import WidgetMetaclass
from hrenpack.type_define import is_object
from hrenpack.framework.kivy.screenmanager import Screen
from hrenpack.framework.kivy.mixins import WidgetMixin
from hrenpack.framework.kivy.widgets import BoxLayout, FloatLayout

__all__ = ['MultiScreenModeFloatLayout', 'MultiScreenModeBoxLayout', 'MultiScreenModeScreen']


class MultiScreenModeMeta(ABCMeta, WidgetMetaclass):
    """Metaclass for MultiScreenMode widgets"""
    pass


class MultiScreenModeBoxLayout(ABC, BoxLayout, metaclass=MultiScreenModeMeta):
    @abstractmethod
    def __init__(self, app, screen, orientation: Literal['vertical', 'horizontal'] = 'vertical',
                 with_view: bool = False, **kwargs):
        super().__init__(orientation, **kwargs)
        self.app = app
        self.screen = screen
        if not with_view:
            self.screen.add_widget(self)


class MultiScreenModeFloatLayout(ABC, FloatLayout, metaclass=MultiScreenModeMeta):
    @abstractmethod
    def __init__(self, app, screen, with_view: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.screen = screen
        if not with_view:
            self.screen.add_widget(self)


class MultiScreenModeScreen(ABC, Screen, metaclass=MultiScreenModeMeta):
    @abstractmethod
    def __init__(self, app, child, orientation: Literal['vertical', 'horizontal'] = 'vertical',
                 with_view: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        if issubclass(child, MultiScreenModeBoxLayout) and not is_object(child):
            self.layout = child(app, self, orientation=orientation, with_view=with_view)


# def get_app(widget, max_path: int = 20):
#     ps = 0
#     if not isinstance(widget, WidgetMixin):
#         raise TypeError(f'widget must be of type WidgetMixin')
#     while True:
#         try:
#             if ps == 0:
#                 return widget.app
#             elif ps > max_path:
#                 raise RecursionError('Max path reached')
#             else:
#                 return eval(f"widget.{'.'.join(['parent'] * ps)}.app")
#         except AttributeError:
#             ps += 1
