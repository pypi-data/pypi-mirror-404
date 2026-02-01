from django.apps import AppConfig


class AdviseConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "nomnom.advise"

    def ready(self) -> None:
        self.enable_signals()

        return super().ready()

    def enable_signals(self):
        from . import (
            receivers,  # noqa: F401
        )
