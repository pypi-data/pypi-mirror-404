import json
import sys

from rich.console import Console

from content_studio.settings import cs_settings

console = Console()


def log(*args, **kwargs):
    console.print(*args, **kwargs)


def flatten(xss):
    return [x for xs in xss for x in xs]


def is_runserver():
    """
    Checks if the Django application is started as a server.
    We'll also assume it started if manage.py is not used (e.g. when Django is started using wsgi/asgi).
    The main purpose of this check is to not run certain code on other management commands such
    as `migrate`.
    """
    is_manage_cmd = sys.argv[0].endswith("/manage.py")

    return not is_manage_cmd or sys.argv[1] == "runserver"


def is_jsonable(x):
    try:
        json.dumps(x)
        return True
    except (TypeError, OverflowError):
        return False


def get_related_field_name(inline, parent_model):
    """
    Get the name of the foreign key field in the inline model.
    """
    if inline.fk_name:
        return inline.fk_name

    # Let Django figure it out

    opts = inline.model._meta

    # Find all foreign keys pointing to parent model
    fks = [
        f
        for f in opts.get_fields()
        if f.many_to_one and f.remote_field.model == parent_model
    ]

    if len(fks) == 1:
        return fks[0].name
    elif len(fks) == 0:
        raise ValueError(
            f"No foreign key found in {inline.model} pointing to {parent_model}"
        )
    else:
        raise ValueError(f"Multiple foreign keys found. Specify fk_name on the inline.")


def get_tenant_field_name(model):
    tenant_model = cs_settings.TENANT_MODEL

    if not tenant_model:
        return None

    opts = model._meta

    # Find all foreign keys pointing to the tenant model
    fks = [
        f
        for f in opts.get_fields()
        if f.many_to_one and f.remote_field.model == tenant_model
    ]

    if len(fks) == 1:
        return fks[0].name
    elif len(fks) == 0:
        return None
    else:
        raise ValueError(
            f"Multiple fields found pointing to {tenant_model}. Only one field can point to a tenant model."
        )
