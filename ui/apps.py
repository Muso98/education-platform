# ui/apps.py
from django.apps import AppConfig


class UiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ui"

    def ready(self):
        """
        Django ilovasi yuklanganda signal modulini avtomatik ulaydi.
        """
        from . import signals  # signalni import qilib, post_save listenerlarni aktivlashtiradi
