from django.conf import settings
from django.utils.decorators import classonlymethod
from django.utils.deprecation import MiddlewareMixin
from django.views.generic.base import ContextMixin, TemplateResponseMixin
from hrenpack import NullStr
from hrenpack.encapsulation import add_attrs_from_dict
from hrenpack.framework.django import view_dict, get_view_app


class DataMixin:
    """Использовать в случае несовместимости с классами View и TemplateView"""
    title: str
    h1_title: NullStr = None

    def get_context_data(self, **kwargs):
        try:
            kwargs = super().get_context_data(**kwargs)
        except AttributeError as error:
            raise error
        kwargs['title'] = self.title
        kwargs['h1_title'] = self.h1_title
        return view_dict(**kwargs)


class NonAbstractMixin:
    @classonlymethod
    def as_view(cls, **initkwargs):
        add_attrs_from_dict(cls, title=initkwargs.get('title', None), h1_title=initkwargs.get('h1_title', None))
        return super().as_view(**initkwargs)


class ModelManagerMixin:
    model_manager = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.model_manager is None:
            self.model_manager = self.model


class SuccessURLMixin:
    success_url: str

    def get_success_url(self):
        return self.success_url


class UserAuthorizeMixin:
    authorize: bool = False

    def get_context_data(self, **kwargs):
        kwargs['authorize'] = self.authorize
        return super().get_context_data(**kwargs)

    @classonlymethod
    def as_view(cls, **initkwargs):
        authorize = initkwargs.get('authorize', False)
        if authorize and not cls.authorize:
            cls.authorize = True
        return super().as_view(**initkwargs)


class TemplateViewMixin(ContextMixin, TemplateResponseMixin):
    pass
