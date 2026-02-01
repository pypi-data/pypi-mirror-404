import inspect

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.relations import RelatedField

user_model = get_user_model()


class ContentRelatedField(RelatedField):

    def to_representation(self, value):
        from content_studio.settings import cs_settings

        admin_site = cs_settings.ADMIN_SITE
        data = {"id": value.id, "__str__": str(value)}

        # Add file URL and media type if the model is a media library model.
        if value.__class__ is cs_settings.MEDIA_LIBRARY_MODEL:
            data["file"] = value.file.url
            data["type"] = value.type
            data["thumbnail"] = admin_site.get_thumbnail(value)

        return data

    def to_internal_value(self, data):
        return self.get_queryset().get(id=data["id"])


class ContentSerializer(serializers.ModelSerializer):
    __str__ = serializers.CharField(read_only=True)
    serializer_related_field = ContentRelatedField

    def get_field_names(self, declared_fields, info):
        """
        Override to automatically add model properties to the fields list.
        """
        # Get the default fields from parent class
        fields = super().get_field_names(declared_fields, info)

        # If fields is '__all__', we need to expand it
        if fields == "__all__":
            fields = list(super().get_field_names(declared_fields, info))
        else:
            fields = list(fields)

        # Get all properties from the model
        model_properties = self._get_model_properties()

        # Add properties that aren't already in fields
        for prop_name in model_properties:
            if prop_name not in fields and prop_name not in declared_fields:
                fields.append(prop_name)

        return fields

    def _get_model_properties(self):
        """
        Extract all @property attributes from the model class.
        """
        model = self.Meta.model
        properties = []

        # Inspect the model class and its parent classes
        for klass in inspect.getmro(model):
            if klass == object:
                break

            for name, obj in inspect.getmembers(klass):
                # Check if it's a property and not private/protected
                if isinstance(obj, property) and not name.startswith("_"):
                    if name not in properties:
                        properties.append(name)

        return properties

    def build_property_field(self, field_name, model_class):
        """
        Create a ReadOnlyField for property attributes.
        """
        return serializers.ReadOnlyField, {}

    def build_field(self, field_name, info, model_class, nested_depth):
        """
        Override to handle property fields.
        """
        # Check if this is a property
        if hasattr(model_class, field_name):
            attr = getattr(model_class, field_name)
            if isinstance(attr, property):
                return self.build_property_field(field_name, model_class)

        # Fall back to default behavior for regular fields
        return super().build_field(field_name, info, model_class, nested_depth)


class RelatedItemSerializer(serializers.Serializer):
    """
    Serializer for use in the relations endpoint.
    """

    id = serializers.UUIDField()
    __str__ = serializers.CharField()


class SessionUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source=user_model.USERNAME_FIELD)

    class Meta:
        model = user_model
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
        )


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = user_model
        fields = (
            "id",
            "first_name",
            "last_name",
        )
