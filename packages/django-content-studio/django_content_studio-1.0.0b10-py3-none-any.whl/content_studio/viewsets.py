import operator
import uuid
from functools import reduce

from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.parsers import JSONParser
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .filters import LookupFilter
from .serializers import RelatedItemSerializer
from .settings import cs_settings
from .utils import get_tenant_field_name


class BaseModelViewSet(ModelViewSet):
    lookup_field = "id"
    is_singleton = False
    parser_classes = [JSONParser]
    renderer_classes = [JSONRenderer]
    permission_classes = [DjangoModelPermissions]
    filter_backends = [SearchFilter, OrderingFilter, LookupFilter]

    def __init__(self, *args, **kwargs):
        super(BaseModelViewSet, self).__init__()
        admin_site = cs_settings.ADMIN_SITE

        self.authentication_classes = [
            admin_site.token_backend.active_backend.authentication_class
        ]

    def list(self, request, *args, **kwargs):
        """
        We overwrite the list method to support singletons. If a singleton
        doesn't exist this will raise a NotFound exception.
        """
        if self.is_singleton:
            return super().retrieve(request, *args, **kwargs)

        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        instance = serializer.save()
        tenant_id = self.request.headers.get("x-dcs-tenant", None)
        tenant_model = cs_settings.TENANT_MODEL
        tenant_field_name = get_tenant_field_name(instance)

        if tenant_model and tenant_id and tenant_field_name:
            setattr(instance, f"{tenant_field_name}_id", tenant_id)

        if hasattr(instance, cs_settings.CREATED_BY_ATTR):
            setattr(instance, cs_settings.CREATED_BY_ATTR, self.request.user)

        content_type = ContentType.objects.get_for_model(instance)
        LogEntry.objects.create(
            user=self.request.user,
            action_flag=ADDITION,
            content_type=content_type,
            object_id=instance.id,
            object_repr=str(instance)[:200],
            change_message="",
        )

        instance.save()

    def perform_update(self, serializer):
        instance = serializer.save()

        if hasattr(instance, cs_settings.EDITED_BY_ATTR):
            setattr(instance, cs_settings.EDITED_BY_ATTR, self.request.user)
            instance.save()

        content_type = ContentType.objects.get_for_model(instance)
        LogEntry.objects.create(
            user=self.request.user,
            action_flag=CHANGE,
            content_type=content_type,
            object_id=instance.id,
            object_repr=str(instance)[:200],
            change_message="",
        )

    def perform_destroy(self, instance):
        content_type = ContentType.objects.get_for_model(instance)
        LogEntry.objects.create(
            user=self.request.user,
            action_flag=DELETION,
            content_type=content_type,
            object_id=instance.id,
            object_repr=str(instance)[:200],
            change_message="",
        )

        instance.delete()

    def get_object(self):
        """
        We overwrite this method to add support for singletons.
        If a singleton doesn't exist it will raise a NotFound exception.
        """
        if self.is_singleton:
            singleton = self.get_queryset().first()

            if singleton:
                return singleton
            else:
                raise NotFound()

        return super().get_object()

    @action(
        methods=["get"], detail=True, url_path="components/(?P<component_id>[^/.]+)"
    )
    def get_component(self, request, id, component_id):
        component = self._admin_model.get_component(uuid.UUID(component_id))

        if not component:
            raise NotFound()

        return component.handle_request(obj=self.get_object(), request=request)

    @action(methods=["post"], detail=False, url_path="relations/(?P<field_name>[^/]+)")
    def get_related_objects(self, request, field_name):
        """
        Endpoint for retrieving related objects.
        """
        search = request.data.get("search", "")

        parent_model = self.queryset.model

        try:
            related_field = parent_model._meta.get_field(field_name)
        except LookupError:
            raise ValidationError("Related field not found.")

        related_model = related_field.related_model

        custom_filter_method = getattr(
            self._admin_model, f"get_related_{field_name}", None
        )

        if custom_filter_method:
            qs = custom_filter_method(
                search=search,
                form_data=request.data.get("form", {}),
                related_model=related_model,
                request=request,
            )

        else:
            char_fields = [
                f.name
                for f in related_model._meta.get_fields()
                if isinstance(f, models.CharField)
            ]

            queries = [Q(**{f"{f}__icontains": search}) for f in char_fields]

            combined_query = reduce(operator.or_, queries)

            qs = related_model.objects.filter(combined_query)

        serializer = RelatedItemSerializer(qs[:20], many=True)

        return Response(data=serializer.data)
