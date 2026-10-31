from django.contrib import admin

from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("title", "knowledge_base", "chat_model", "updated_at")
    list_filter = ("chat_model", "knowledge_base")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "role", "model_used", "created_at")
    list_filter = ("role",)
    search_fields = ("content",)
