from rest_framework.routers import DefaultRouter


class ExtendedRouter(DefaultRouter):
    def get_method_map(self, viewset, method_map):
        _method_map = super().get_method_map(viewset, method_map)

        if getattr(viewset, "is_singleton", False):
            _method_map["patch"] = "update"

        return _method_map


content_studio_router = ExtendedRouter(trailing_slash=False)
