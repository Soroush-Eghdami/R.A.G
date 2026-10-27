from django.contrib import admin

from .models import Document, KnowledgeBase


@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ("name", "embedding_model", "chunk_size", "chunk_overlap", "created_at")
    search_fields = ("name", "description")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "original_name",
        "knowledge_base",
        "status",
        "chunk_count",
        "size_bytes",
        "created_at",
    )
    list_filter = ("status", "file_type", "knowledge_base")
    search_fields = ("original_name", "sha256")
    readonly_fields = ("sha256", "created_at", "updated_at")
