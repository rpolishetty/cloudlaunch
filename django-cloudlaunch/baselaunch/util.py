import operator

from django.conf.urls import url
from rest_framework import routers, viewsets
from rest_framework_nested import routers as nested_routers


class HybridRoutingMixin(object):
    """
    Extends functionality of DefaultRouter adding possibility to register
    simple API views, not just Viewsets.
    Based on:
    http://stackoverflow.com/questions/18818179/routing-api-views-in-django-rest-framework
    http://stackoverflow.com/questions/18817988/using-django-rest-frameworks-browsable-api-with-apiviews
    """

    def get_routes(self, viewset):
        """
        Checks if the viewset is an instance of ViewSet, otherwise assumes
        it's a simple view and does not run original `get_routes` code.
        """
        if issubclass(viewset, viewsets.ViewSetMixin):
            return super(HybridRoutingMixin, self).get_routes(viewset)

        return []

    def get_urls(self):
        """
        Append non-viewset views to the urls generated by the original `get_urls` method.
        """
        # URLs for viewsets
        ret = super(HybridRoutingMixin, self).get_urls()

        # URLs for simple views
        for prefix, viewset, basename in self.registry:

            # Skip viewsets
            if issubclass(viewset, viewsets.ViewSetMixin):
                continue

            # URL regex
            regex = '{prefix}{trailing_slash}$'.format(
                prefix=prefix,
                trailing_slash=self.trailing_slash
            )

            # The view name has to have suffix "-list" due to specifics
            # of the DefaultRouter implementation.
            ret.append(
                url(regex, viewset.as_view(), name='{0}-list'.format(basename)))

        return ret


class HybridDefaultRouter(HybridRoutingMixin, routers.DefaultRouter):
    pass


class HybridSimpleRouter(HybridRoutingMixin, routers.SimpleRouter):
    pass


class HybridNestedRouter(HybridRoutingMixin, nested_routers.NestedSimpleRouter):
    pass


def getattrd(obj, name):
    """
    Same as ``getattr()``, but allows dot notation lookup.
    """
    try:
        return operator.attrgetter(name)(obj)
    except AttributeError:
        return None
