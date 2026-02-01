import uuid

from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from content_studio.settings import cs_settings


class Dashboard:
    """
    The Dashboard class is used to define the structure of the dashboard
    in Django Content Studio.
    """

    widgets = None

    def __init__(self, **kwargs):
        self.widgets = kwargs.get("widgets", [])

    def set_up_router(self):
        from content_studio.router import content_studio_router

        content_studio_router.register(
            "api/dashboard",
            DashboardViewSet,
            basename="content_studio_dashboard",
        )

    def serialize(self):
        return {
            "widgets": [
                {
                    "name": w.name,
                    "widget_id": w.widget_id,
                    "col_span": w.col_span,
                }
                for w in self.widgets
            ]
        }


class DashboardViewSet(ViewSet):
    parser_classes = [JSONParser]
    renderer_classes = [JSONRenderer]

    def __init__(self, *args, **kwargs):
        super(ViewSet, self).__init__()
        admin_site = cs_settings.ADMIN_SITE

        self.dashboard = admin_site.dashboard
        self.authentication_classes = [
            admin_site.token_backend.active_backend.authentication_class
        ]

    @action(detail=False, url_path="widgets/(?P<widget_id>[^/.]+)")
    def get(self, request, widget_id=None):
        widget = None

        for w in self.dashboard.widgets:
            if widget_id == str(w.widget_id):
                widget = w

        if not widget:
            raise NotFound()

        data = widget.get_data(request)

        if isinstance(data, serializers.Serializer):
            data.is_valid(raise_exception=True)
            data = data.data

        return Response(data=data)


class BaseWidget:
    col_span = 1
    widget_id = None

    def __init__(self):
        self.widget_id = self.widget_id or uuid.uuid4()


class SpacingWidget(BaseWidget):
    name = "SpacingWidget"

    def __init__(self, col_span=1):
        self.col_span = col_span
        super().__init__()
