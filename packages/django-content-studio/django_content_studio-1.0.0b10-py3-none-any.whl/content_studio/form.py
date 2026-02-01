###
# Form field classes are used for grouping, ordering and laying out fields.
###
import uuid
from typing import Type

from django.db.models import Model
from rest_framework.response import Response


class Field:
    """
    Field class for configuring the fields in content edit views in Django Content Studio.
    """

    def __init__(self, name: str, col_span: int = 1, label: str = None):
        self.name = name
        self.col_span = col_span
        self.label = label

    def serialize(self):
        return {
            "type": "field",
            "name": self.name,
            "col_span": self.col_span,
            "label": self.label,
        }


class FieldLayout:
    """
    Field layout class for configuring the layout of fields in content edit views in Django Content Studio.
    """

    def __init__(self, fields: list[str | Field] = None, columns: int = 1):
        self.fields = [self._normalize_field(f) for f in fields] if fields else []
        self.columns = columns

    def serialize(self):
        return {
            "type": "field-layout",
            "fields": [field.serialize() for field in self.fields],
            "columns": self.columns,
        }

    def get_fields(self) -> list[Field]:
        return self.fields

    def _normalize_field(self, field):
        """
        Checks if a field is of an allowed type and wraps string fields in a Field object.
        """
        if isinstance(field, str):
            return Field(field)
        elif isinstance(field, Field):
            return field
        else:
            raise ValueError(f"Invalid field: {field}. Must be a string or Field.")


class FormSet:
    """
    Formset class for configuring the blocks of fields in content edit views
    in Django Content Studio.
    """

    def __init__(
        self,
        title: str = "",
        description: str = "",
        fields: list[str | Field | FieldLayout] = None,
    ):
        self.title = title
        self.description = description
        self.fields = [self._normalize_field(f) for f in fields] if fields else []

    def serialize(self):
        return {
            "type": "form-set",
            "title": self.title,
            "description": self.description,
            "fields": [field.serialize() for field in self.fields],
        }

    def get_fields(self) -> list[Field]:
        """
        Returns a list of all Field and Component objects.
        """
        fields = []

        for field in self.fields:
            if isinstance(field, FieldLayout):
                fields = fields + field.get_fields()
            else:
                fields.append(field)

        return fields

    def _normalize_field(self, field):
        """
        Checks if a field is of an allowed type and wraps string fields in a Field object.
        """
        if isinstance(field, str):
            return Field(field)
        elif isinstance(field, Field):
            return field
        elif isinstance(field, FieldLayout):
            return field
        elif issubclass(field.__class__, Component):
            return field
        else:
            raise ValueError(
                f"Invalid field: {field}. Must be a string, Field, FieldLayout or a Component (subclass)."
            )


class FormSetGroup:
    """
    Formset group class for configuring the groups of form sets in content edit views.
    """

    def __init__(self, label: str = "", formsets: list[FormSet] = None):
        self.label = label
        self.formsets = formsets or []

    def serialize(self):
        return {
            "type": "form-set-group",
            "label": self.label,
            "formsets": [formset.serialize() for formset in self.formsets],
        }

    def get_fields(self) -> list[Field]:
        """
        Returns a list of all Field and Component objects.
        """
        fields = []

        for form_set in self.formsets:
            fields = fields + form_set.get_fields()

        return fields


class Component:
    component_id: uuid.UUID
    component_type: str

    def __init__(self):
        self.component_id = uuid.uuid4()

    def serialize(self):
        return {
            "type": "component",
            "component_type": str(self.component_type),
            "component_id": str(self.component_id),
        }


class Link(Component):
    component_type = "Link"
    label: str

    def get_url(self, obj: Type[Model], request):
        raise NotImplementedError

    def serialize(self):
        return {
            **super().serialize(),
            "label": self.label,
        }

    def handle_request(self, obj: Type[Model], request):
        return Response(data={"url": self.get_url(obj, request)})


class ButtonLink(Link):
    component_type = "LinkButton"

    # Add icon before label
    icon = None

    # Add copy to clipboard button
    copy = False

    def serialize(self):
        return {
            **super().serialize(),
            "icon": self.icon,
            "copy": self.copy,
        }
