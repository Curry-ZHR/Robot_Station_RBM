"""Managed runtime services for Robot Station."""

from modules.runtime.service_manager import ServiceManager


_manager = ServiceManager.with_default_services()


def get_service_manager():
    return _manager


def shutdown_services():
    _manager.shutdown()

