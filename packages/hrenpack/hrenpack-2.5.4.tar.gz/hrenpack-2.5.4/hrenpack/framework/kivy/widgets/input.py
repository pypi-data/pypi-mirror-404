from typing import Optional, Union
from kivy.graphics import Color, Rectangle
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner as KivyComboBox
from kivy.uix.togglebutton import ToggleButton as KivyToggleButton
from kivy.uix.checkbox import CheckBox as KivyCheckBox
from kivy.uix.textinput import TextInput as KivyTextInput
from hrenpack.framework.kivy import rgba
from hrenpack.framework.kivy.mixins import WidgetMixin
from hrenpack.listwork import key_in_dict

_rgb_type = Union[tuple[int, int, int], tuple[int, int, int, int]]


class ComboBox(KivyComboBox, WidgetMixin):
    def __init__(self, parent=None, *elements, index: int = 0, command=None, **kwargs):
        elements = list(elements)
        if not key_in_dict(kwargs, 'text'):
            kwargs['text'] = elements[index]
        super(ComboBox, self).__init__(values=elements, **kwargs)
        if parent is not None:
            parent.add_widget(self)
        if command is not None:
            self.connect(command)

    def connect(self, command):
        self.bind(text=command)

    def append(self, element: str):
        self.values.append(element)

    def index(self, element: str):
        return self.values.index(element)

    def get_selected(self):
        try:
            return self.index(self.text)
        except ValueError:
            return None

    def set_selected(self, index: int):
        self.text = self.values[index]


class CustomBackgroundComboBox(ComboBox):
    """Находится в разработке, используйте на свой страх и риск"""
    class _DropDown(DropDown):
        def __init__(self, parent, background_color, **kwargs):
            super().__init__(**kwargs)
            self._background_color = background_color
            self.parent_ = parent
            with self.canvas.before:
                Color(*self.background_color)
                self.rect = Rectangle(size=self.size, pos=self.pos)

            self.bind(size=self._update_rect, pos=self._update_rect)

        @property
        def background_color(self):
            return rgba(*self._background_color)

        @background_color.setter
        def background_color(self, color: _rgb_type):
            self._background_color = color
            with self.canvas.before:
                Color(*self.background_color)

        def _update_rect(self, instance, value):
            self.rect.pos = self.pos
            self.rect.size = self.size

    def __init__(self,  parent=None, background_color: Optional[_rgb_type] = None, *elements, index: int = 0,
                 command=None, **kwargs):
        super(CustomBackgroundComboBox, self).__init__(parent, *elements, index=index, command=command, **kwargs)
        self._dropdown = self._DropDown(self, background_color)
        self._background_color = background_color if background_color is not None else super().background_color

    def _on_drop_down(self, combobox, dropdown):
        with combobox.canvas.before:
            Color(*self.background_color)
            Rectangle(size=combobox.size, pos=combobox.pos)

    @property
    def background_color(self):
        return rgba(*self._background_color)

    @background_color.setter
    def background_color(self, color: _rgb_type):
        self._background_color = color
        self._dropdown.background_color = color


class ToggleButtonGroup:
    def __init__(self, name: str, parent=None, command=None, **kwargs):
        self._name = name
        self._buttons = list()
        self._command = command
        self._auto_add_to_parent = kwargs.get('auto_add_to_parent', False)
        self.parent = parent

    def __call__(self, button):
        self._buttons.append(button)
        if self._command is not None:
            button.connect(self._command)
        if button.name is None:
            button.name = str(len(self._buttons) - 1)
        if self.parent is not None and self._auto_add_to_parent:
            self.parent.add_widget(button)
        return self.name

    def __str__(self):
        return self._name

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_name: str):
        self._name = new_name

    def buttons(self) -> list:
        return self._buttons

    def connect(self, command=None):
        if command is None and self._command is not None:
            command = self._command
        elif command is None:
            raise ValueError('Command is None')
        for button in self.buttons():
            button.bind(on_press=command)

    def add_to_parent(self):
        for button in self.buttons():
            self.parent.add_widget(button)

    def get_selected(self):
        for button in self.buttons():
            if button.state == 'down':
                return button.name
        else:
            return None

    def set_selected(self, name):
        for button in self.buttons():
            if button.state == 'down':
                button.state = 'normal'
                continue
            if button.name == name:
                button.state = 'down'
                break
        else:
            raise ValueError(f'No such button: {name}')


class ToggleButton(KivyToggleButton, WidgetMixin):
    _name = None

    def __init__(self, text: str = '', group: Optional[ToggleButtonGroup] = None, parent=None,
                 name: Optional[str] = None, **kwargs):
        super(ToggleButton, self).__init__(text=text, group=group(self), **kwargs)
        if parent is not None:
            parent.add_widget(self)
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_name: str):
        self._name = new_name

    def __str__(self):
        return "ToggleButton('{}')".format(self.name)

    def connect(self, command):
        """Не рекомендуется к использованию, лучше использовать group.connect(command)"""
        self.bind(on_press=command)


class ToggleButtonWithoutParentInInit(ToggleButton):
    def __init__(self, text: str = '', group: Optional[ToggleButtonGroup] = None, name: Optional[str] = None, **kwargs):
        super().__init__(text, group, name=name, **kwargs)


class CheckBox(KivyCheckBox, WidgetMixin):
    def __init__(self, parent=None, command=None, checked: bool = False, **kwargs):
        super(CheckBox, self).__init__(**kwargs)
        if parent is not None:
            parent.add_widget(self)
        if command is not None:
            self.connect(command)
        if checked:
            self.active = True
        self.get_selected = self.is_selected

    def connect(self, command):
        self.bind(active=command)

    def is_selected(self):
        return self.active

    def set_selected(self, active: Optional[bool] = None):
        if active is None:
            self.active = not self.active
        else:
            self.active = active


class TextInput(KivyTextInput, WidgetMixin):
    def __init__(self, parent=None, command=None, placeholder: str = '', multiline: bool = False, **kwargs):
        super().__init__(hint_text=placeholder, multiline=multiline, **kwargs)
        if parent is not None:
            parent.add_widget(self)
        if command is not None:
            self.connect(command)

    @property
    def placeholder(self) -> str:
        return self.hint_text

    @placeholder.setter
    def placeholder(self, new_placeholder: str):
        self.hint_text = new_placeholder

    def get_text(self):
        return self.text

    def set_text(self, text):
        self.text = text

    def connect(self, command):
        self.bind(text=command)
