from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.settings import api_settings as simplejwt_settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView


class SimpleJwtViewSet(ViewSet):
    @action(
        detail=False, methods=["post"], permission_classes=[], authentication_classes=[]
    )
    def refresh(self, request):

        view_instance = TokenRefreshView()
        view_instance.request = request
        view_instance.format_kwarg = None
        return view_instance.post(request)


class SimpleJwtBackend:
    name = "Simple JWT"
    authentication_class = JWTAuthentication
    view_set = SimpleJwtViewSet

    @classmethod
    def get_info(cls):

        return {
            "type": cls.__name__,
            "config": {
                "ACCESS_TOKEN_LIFETIME": simplejwt_settings.ACCESS_TOKEN_LIFETIME.total_seconds(),
            },
        }

    @property
    def is_available(self) -> bool:
        try:
            import rest_framework_simplejwt

            return True
        except ImportError:
            return False

    @classmethod
    def get_response_for_user(cls, user):

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
        )
