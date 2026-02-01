from django.urls import re_path

from .media_library.viewsets import MediaLibraryViewSet, MediaFolderViewSet
from .router import content_studio_router
from .views import ContentStudioWebAppView, AdminApiViewSet

content_studio_router.register("api", AdminApiViewSet, "content_studio_admin")
content_studio_router.register(
    "api/media-library/items", MediaLibraryViewSet, "content_studio_media_library_items"
)
content_studio_router.register(
    "api/media-library/folders",
    MediaFolderViewSet,
    "content_studio_media_library_folders",
)

urlpatterns = [
    re_path(
        "^(?!api).*$", ContentStudioWebAppView.as_view(), name="content_studio_web"
    ),
] + content_studio_router.urls
