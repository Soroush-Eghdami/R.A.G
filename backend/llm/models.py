"""App-wide defaults, stored as a single row."""

from __future__ import annotations

from django.conf import settings
from django.db import models


class AppSettings(models.Model):
    default_chat_model = models.CharField(max_length=200, blank=True)
    default_embedding_model = models.CharField(max_length=200, blank=True)
    top_k = models.PositiveIntegerField(default=4)
    temperature = models.FloatField(default=0.2)
    num_ctx = models.PositiveIntegerField(default=8192)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "app settings"

    def __str__(self) -> str:
        return "App settings"

    def save(self, *args, **kwargs):
        """Always keep one row."""
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> "AppSettings":
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                "top_k": settings.DEFAULT_TOP_K,
                "temperature": settings.DEFAULT_TEMPERATURE,
                "num_ctx": settings.DEFAULT_NUM_CTX,
            },
        )
        return obj
