from django.contrib import admin

from .models import AppSettings


@admin.register(AppSettings)
class AppSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "default_chat_model",
        "default_embedding_model",
        "top_k",
        "num_ctx",
        "updated_at",
    )

    def has_add_permission(self, request):
        return not AppSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
