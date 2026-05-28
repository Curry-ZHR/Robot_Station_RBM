import importlib
from array import array


class RosMessageImportError(RuntimeError):
    pass


def import_message_class(message_type):
    parts = str(message_type).split("/")
    if len(parts) != 3 or parts[1] != "msg":
        raise RosMessageImportError(f"Unsupported ROS message type: {message_type}")

    package, _, class_name = parts
    module_name = f"{package}.msg"
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        raise RosMessageImportError(f"Cannot import ROS message module {module_name}: {exc}") from exc

    try:
        return getattr(module, class_name)
    except AttributeError as exc:
        raise RosMessageImportError(f"Cannot find ROS message class {message_type}") from exc


def import_service_class(service_type):
    parts = str(service_type).split("/")
    if len(parts) != 3 or parts[1] != "srv":
        raise RosMessageImportError(f"Unsupported ROS service type: {service_type}")

    package, _, class_name = parts
    module_name = f"{package}.srv"
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        raise RosMessageImportError(f"Cannot import ROS service module {module_name}: {exc}") from exc

    try:
        return getattr(module, class_name)
    except AttributeError as exc:
        raise RosMessageImportError(f"Cannot find ROS service class {service_type}") from exc


def message_to_plain(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, bytes):
        return list(value)
    if isinstance(value, array):
        return list(value)
    if isinstance(value, (list, tuple)):
        return [message_to_plain(item) for item in value]
    if hasattr(value, "get_fields_and_field_types"):
        return {
            field: message_to_plain(getattr(value, field))
            for field in value.get_fields_and_field_types()
        }
    return str(value)
