import importlib
from urllib.parse import urlencode
from django.apps import apps
from django.conf import settings
from django.contrib.auth import logout, login
from django.core.exceptions import ImproperlyConfigured
from django.db.models import IntegerChoices, Model
from django.forms import Form
from django.http import Http404
from django.shortcuts import render, redirect
from typing import Union, Optional, Any
from dataclasses import dataclass
from django.urls import reverse, reverse_lazy

from hrenpack import NullStr


class Category:
    def __init__(self, name: str, slug: str):
        self.name = name
        self.slug = slug

    def __str__(self):
        return f'name={self.name}, slug={self.slug}'


class HrenpackDjangoError(Exception):
    pass


class MenuElement:
    """Элемент меню"""
    def __init__(self, title: str, href: str = '/'):
        self.href = href
        self.title = title

    def __str__(self):
        return self.title


def view_dict(title: str, h1_title: NullStr = None, **kwargs) -> dict:
    # kwargs['media_url'] = '/media/'
    kwargs['title'] = title
    kwargs['h1_title'] = title if h1_title is None else h1_title
    return kwargs


def boolean_choices(arg: IntegerChoices):
    return tuple(map(lambda x: (bool(x[0]), x[1]), arg.choices))


def semicolon_plus(model, del_id: bool = True):
    output = dict()
    for field in model._meta.fields:
        verbose_name = field.verbose_name + ':'
        name = field.name
        output[name] = verbose_name
    if del_id:
        del output['id']
    return output


class BooleanChoices(IntegerChoices):
    @property
    def choices(self):
        return boolean_choices(self)


def get_view_app(view):
    return view.__module__.split('.')[0]


# def get_view_base_template(view):
#     return getattr(view, 'base_template_name', getattr(settings, 'BASE_TEMPLATE', 'empty.html'))


def get_view_base_template(view):
    # Добавьте проверку на None и пустую строку
    base_template = getattr(view, 'base_template_name', None)
    if not base_template:
        base_template = getattr(settings, 'BASE_TEMPLATE', 'empty.html')
    return base_template or 'empty.html'  # Гарантирует возврат непустого значения


def add_url_GET(base_url: str, request=None, **params):
    if request is not None:
        params.update(request.GET)
    return f'{base_url}?{urlencode(params)}'


def url_or_reverse(url: str, lazy_mode: bool = True, **kwargs):
    if '/' in url:
        return url
    func = reverse_lazy if lazy_mode else reverse
    return func(url, kwargs=kwargs)


def get_app_inclusion_namespace(app_name: str):
    urlpatterns = importlib.import_module(settings.ROOT_URLCONF).urlpatterns
    for pattern in urlpatterns:
        if hasattr(pattern, 'app_name') and pattern.app_name == app_name:
            return pattern.namespace


# def get_model(setting_name: str):
#     setting_name = setting_name.upper()
#     setting = getattr(settings, setting_name)
#     try:
#         return apps.get_model(setting, require_ready=False)
#     except ValueError:
#         raise ImproperlyConfigured(f"{setting_name} must be of the form 'app_label.model_name'")
#     except LookupError:
#         raise ImproperlyConfigured(f"{setting_name} refers to model '%s' that has not been installed" % setting)
