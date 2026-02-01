from django import forms
from django.contrib.auth import forms as auth_forms, password_validation, get_user_model


class PasswordChangeForm(auth_forms.PasswordChangeForm):
    old_password = forms.CharField(
        label="Старый пароль",
        required=False,
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "current-password", "autofocus": True}
        ),
    )

    password1 = forms.CharField(
        label="Новый пароль",
        required=False,
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text=password_validation.password_validators_help_text_html(),
    )

    password2 = forms.CharField(
        label="Подтвердить пароль",
        required=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
        help_text="Для подтверждения введите, пожалуйста, пароль ещё раз.",
    )

    def __bool__(self):
        cd = self.cleaned_data
        return not cd['new_password1'] and cd['new_password2']

    def is_valid(self):
        cd = self.cleaned_data
        if cd['password1'] and cd['password2']:
            pass
        elif cd['password1'] or cd['password2']:
            return False
        return super().is_valid()
