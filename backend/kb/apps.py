from django.apps import AppConfig


class KbConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "kb"

    def ready(self) -> None:
        # Run once on the first request, not at import time (no DB at startup).
        from django.core.signals import request_started
        from django.db.backends.signals import connection_created

        request_started.connect(_recover_documents, dispatch_uid="kb.startup_recovery")
        connection_created.connect(_sqlite_pragmas, dispatch_uid="kb.sqlite_pragmas")


def _sqlite_pragmas(sender, connection, **kwargs) -> None:
    """WAL lets the worker write while requests read."""
    if connection.vendor != "sqlite":
        return
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA busy_timeout=20000;")


def _recover_documents(sender, **kwargs) -> None:
    from django.conf import settings
    from django.core.signals import request_started

    request_started.disconnect(_recover_documents, dispatch_uid="kb.startup_recovery")
    if not getattr(settings, "STARTUP_RECOVERY", True):
        return
    try:
        from .tasks import recover_stuck_documents

        recover_stuck_documents()
    except Exception:  # noqa: BLE001 - startup must never crash
        return
