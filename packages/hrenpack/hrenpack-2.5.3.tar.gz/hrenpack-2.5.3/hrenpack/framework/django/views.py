from typing import Any

from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib.staticfiles.storage import staticfiles_storage
from django.db.models import Model
from django.shortcuts import render, redirect
from django.utils.decorators import classonlymethod
from django.views import View as DjangoView, generic
from django.contrib.auth import views as auth_views, logout, get_user_model, login, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from hrenpack import NullStr
from hrenpack.boolwork import For
from hrenpack.listwork import get_from_dict
from hrenpack.encapsulation import SafeInheritance, addattr, set_attrs_if_is_none
from hrenpack.framework.django import view_dict
from hrenpack.framework.django.forms import PasswordChangeForm, auth_forms
from hrenpack.framework.django.mixins import (NonAbstractMixin, ModelManagerMixin, UserAuthorizeMixin,
                                              TemplateViewMixin)


class BaseView(DjangoView, NonAbstractMixin):
    title: NullStr = None
    h1_title: NullStr = None
    dont_header: bool = False
    _base_template_name: str = getattr(settings, 'BASE_TEMPLATE', 'empty.html')

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['title'] = self.title if self.title else "Страница"
        kwargs['h1_title'] = self.h1_title
        kwargs['dont_header'] = self.dont_header
        kwargs['base_template_name'] = self.base_template_name
        return view_dict(**kwargs)

    @property
    def base_template_name(self):
        return getattr(self, '_base_template_name',
                       getattr(settings, 'BASE_TEMPLATE', 'empty.html'))

    @base_template_name.setter
    def base_template_name(self, value):
        self._base_template_name = value or getattr(settings, 'BASE_TEMPLATE', 'empty.html')

    @classonlymethod
    def as_view(cls, **initkwargs):
        initkwargs.setdefault('title', "Страница")
        set_attrs_if_is_none(cls, **get_from_dict(initkwargs, 'title', 'h1_title', 'template_name',
                                                  'extra_context', pop_mode=True))
        return super().as_view(**initkwargs)


class View(BaseView, TemplateViewMixin):
    pass


class TemplateView(BaseView, generic.TemplateView):
    pass


class ListView(BaseView):
    model: Model
    context_name: str = 'db'

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs[self.context_name] = self.get_queryset()
        return kwargs

    def get_queryset(self):
        return self.model.objects.all()

    # def get_model_dk(self, field: str):
    #     """Возвращает элементы из определенного поля модели"""
    #     if field in self.model._meta.fields:
    #         output = list()
    #         for el in self.get_queryset():
    #             output.append(el.__dict__[field])
    #         return output
    #     else:
    #         raise AttributeError("Указанного поля модели не существует")
    #
    # def get_object_or_404(self, field: str, value) -> Model:
    #     """Возвращает объект модели. Если нет, то возвращает исключение 404"""
    #     elements = self.get_queryset()
    #     values = self.get_model_dk(field)
    #     if not value in values:
    #         raise Http404
    #     return elements.get(**{field: value})


class DetailView(ModelManagerMixin, BaseView, generic.DetailView):
    pass


class FormView(BaseView, generic.FormView):
    pass


class CreateView(BaseView, generic.CreateView):
    pass


class UpdateView(ModelManagerMixin, BaseView, generic.UpdateView):
    pass


class PasswordChangeView(BaseView, auth_views.PasswordChangeView):
    pass


class PasswordChangeDoneView(BaseView, auth_views.PasswordChangeDoneView):
    pass


class PasswordResetView(BaseView, auth_views.PasswordResetView):
    pass


class PasswordResetDoneView(BaseView, auth_views.PasswordResetDoneView):
    pass


class PasswordResetConfirmView(BaseView, auth_views.PasswordResetConfirmView):
    pass


class PasswordResetCompleteView(UserAuthorizeMixin, BaseView, auth_views.PasswordResetCompleteView):
    pass


class LoginView(BaseView, auth_views.LoginView):
    title = "Авторизация"


class LogoutView(BaseView, auth_views.LogoutView):
    title = "Вы вышли из аккаунта"


def create_logout_view(template_name: str, title: str = "Вы вышли из аккаунта", h1_title: NullStr = None,
                       dont_header: bool = False, **kwargs):
    def logout_view(request):
        logout(request)
        return render(request, template_name, view_dict(title, h1_title, dont_header=dont_header, **kwargs))
    return logout_view


def create_logout_view_with_next():
    def logout_view(request):
        if request.user.is_authenticated:
            logout(request)
        return redirect(request.GET.get('next', '/'))
    return logout_view


class RegistrationView(CreateView):
    title = "Регистрация"
    model = get_user_model()
    form_class = UserCreationForm

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


# class EditProfileView(View, LoginRequiredMixin):
#     profile_form_class: Any
#     password_change_form_class: Any = PasswordChangeForm
#     success_url: Any
#     title = "Изменить настройки пользователя"
#
#     def __new__(cls, *args, **kwargs):
#         if not issubclass(cls.password_change_form_class, PasswordChangeForm):
#             raise TypeError
#         return super().__new__(cls, *args, **kwargs)
#
#     def get(self, request, *args, **kwargs):
#         user_profile_form = self.profile_form_class(instance=request.user)
#         password_change_form = self.password_change_form_class(user=request.user)
#         return render(request, self.template_name, view_dict(
#             self.title, self.h1_title,
#             user_profile_form=user_profile_form,
#             password_change_form=password_change_form,
#             pur=True
#         ))
#
#     def post(self, request, *args, **kwargs):
#         user_profile_form = self.profile_form_class(request.POST, instance=request.user)
#         password_change_form = self.password_change_form_class(user=request.user, data=request.POST)
#         password_form_is_empty = self._password_form_is_empty(password_change_form)
#
#         if user_profile_form.is_valid() and any((password_change_form.is_valid(), password_form_is_empty)):
#             user_profile_form.save()
#             if password_form_is_empty:
#                 user = password_change_form.save()
#                 update_session_auth_hash(request, user)  # Обновляем сессию, чтобы не разлогинивать пользователя
#             return redirect(self.success_url)  # Замените на нужный вам URL
#
#         return render(request, self.template_name, view_dict(
#             self.title, self.h1_title,
#             user_profile_form=user_profile_form,
#             password_change_form=password_change_form,
#             pur=password_form_is_empty
#         ))
#
#     @staticmethod
#     def _password_form_is_empty(form):
#         cd = form.cleaned_data
#         return not cd['new_password1'] and cd['new_password2']
#
#
# class DirectoryView(View, NonAbstractMixin):
#     path: str
#
#     def get_context_data(self, **kwargs):
#         pass


class StaticFileView(generic.RedirectView):
    @classonlymethod
    def as_view(cls, **initkwargs):
        path = initkwargs.pop('path')
        if path is None:
            raise KeyError('path')
        return super().as_view(url=staticfiles_storage.url(path), **initkwargs)
