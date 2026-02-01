from wtforms import SelectField
from wtforms.validators import ValidationError


class BooleanSelectField(SelectField):
    """
    SelectField, который принимает 'true'/'false' в HTML,
    но возвращает bool в data
    """

    def __init__(self, label='', validators=None,
                 false_label: str = "Ложь",
                 true_label: str = "Истина",
                 **kwargs):
        # Устанавливаем стандартные choices
        choices = [('false', false_label), ('true', true_label)]

        # Позволяем переопределить choices, если нужно
        if 'choices' not in kwargs:
            kwargs['choices'] = choices

        # Не используем coerce=bool, так как он не работает с 'true'/'false'
        kwargs.pop('coerce', None)

        super().__init__(label, validators, **kwargs)

        # Сохраняем текстовые значения для валидации
        self.true_value = 'true'
        self.false_value = 'false'

    def process_formdata(self, valuelist):
        """
        Обрабатывает данные из формы
        """
        if valuelist:
            value = str(valuelist[0])
            # Преобразуем строку в bool
            if value == self.true_value:
                self.data = True
            elif value == self.false_value:
                self.data = False
            else:
                self.data = None
                raise ValidationError(f'Недопустимое значение: {value}')

            # ВАЖНО: сохраняем raw_data для валидации choices
            self.raw_data = [value]
        else:
            self.data = None
            self.raw_data = []

    def pre_validate(self, form):
        """
        Переопределяем валидацию, чтобы пропустить стандартную проверку choices
        Вместо этого проверяем, что значение True или False
        """
        # Пропускаем стандартную валидацию choices
        if self.data is not None and self.data in (True, False):
            return
        elif self.data is None and not self.raw_data:
            # Пустое значение
            pass
        else:
            raise ValidationError(self.gettext('Not a valid choice'))

    def _value(self):
        """
        Возвращает значение для отображения в HTML
        """
        if self.data is True:
            return self.true_value
        elif self.data is False:
            return self.false_value
        return ''
