import logging
from typing import Optional
from hrenpack.listwork import key_in_dict
from hrenpack.kwargswork import get_kwarg
from hrenpack.framework.kivy.widgets import BoxLayout, Label, input


class TextCheckBox(BoxLayout):
    class CheckBox(input.CheckBox):
        @property
        def pos_x(self):
            return self.pos[0]

        @pos_x.setter
        def pos_x(self, value):
            pos_y = self.pos[1]
            self.pos = (value, pos_y)
            self.parent._set_label_pos_x(value + self.parent._difference)  # Ссылка на разницу родителя

    class Label(Label):
        @property
        def pos_x(self):
            return self.pos[0]

        @pos_x.setter
        def pos_x(self, value):
            pos_y = self.pos[1]
            self.pos = (value, pos_y)

    def __init__(self, text: str, parent=None, command=None, checked: bool = False, difference: float = 5, **kwargs):  # Настраиваемая разница
        if key_in_dict(kwargs, 'vert'):
            vert = kwargs['vert']
            del kwargs['vert']
        else:
            vert = False
        orientation = 'vertical' if vert else 'horizontal'
        checkbox_kwargs = get_kwarg(kwargs, 'checkbox_kwargs', {}, False, True)
        label_kwargs = get_kwarg(kwargs, 'label_kwargs', {}, False, True)
        super().__init__(orientation, parent, padding=difference, **kwargs)
        self._difference_ = difference
        self.checkbox = input.CheckBox(self, command, checked, **checkbox_kwargs)
        self.label = Label(text, self, **label_kwargs)
        self.get_selected = self.is_selected

    @property
    def _difference(self):
        return self._difference_

    @_difference.setter
    def _difference(self, value):
        self._difference_ = value
        self.padding = value

    def is_selected(self):
        return self.checkbox.is_selected()

    def set_selected(self, active: Optional[bool] = None):
        self.checkbox.set_selected(active)

    def _set_label_pos_x(self, pos_x: float):
        self.label.pos_x = pos_x + self._difference  # Используйте разницу, заданную в конструкторе


class DoubleWidget(BoxLayout):
    def __init__(self, child1, child2, parent, **kwargs):
        super().__init__('vertical', parent, **kwargs)
        self.child1 = child1
        self.child2 = child2

        self.add_widget(self.child1)

    def switch(self, *args):
        if self.child1 in self.children:
            self.switch2(*args)
        else:
            self.switch1(*args)

    def switch1(self, *args):
        if self.child2 in self.children:
            self.remove_widget(self.child2)
            self.add_widget(self.child1)
        else:
            logging.debug("Уже активирован первый виджет")

    def switch2(self, *args):
        if self.child1 in self.children:
            self.remove_widget(self.child1)
            self.add_widget(self.child2)
        else:
            logging.debug("Уже активирован второй виджет")
