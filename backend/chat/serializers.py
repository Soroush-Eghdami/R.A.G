"""Conversation, message and ask payloads."""

from __future__ import annotations

from django.conf import settings
from llm.models import AppSettings
from rest_framework import serializers

from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "role", "content", "sources", "model_used", "created_at"]
        read_only_fields = fields


class ConversationSerializer(serializers.ModelSerializer):
    # Optional: falls back to AppSettings, then to DEFAULT_CHAT_MODEL.
    chat_model = serializers.CharField(required=False, allow_blank=True)
    messages = MessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "knowledge_base",
            "title",
            "chat_model",
            "message_count",
            "messages",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_message_count(self, obj: Conversation) -> int:
        return obj.messages.count()

    def validate(self, attrs):
        if self.instance is None and not attrs.get("chat_model"):
            defaults = AppSettings.load()
            attrs["chat_model"] = defaults.default_chat_model or settings.DEFAULT_CHAT_MODEL
            if not attrs["chat_model"]:
                raise serializers.ValidationError(
                    {"chat_model": "Pick a chat model from /api/models/."}
                )
        return attrs


class AskSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=8000, trim_whitespace=True)
    stream = serializers.BooleanField(default=True, required=False)
    think = serializers.BooleanField(default=False, required=False)
    top_k = serializers.IntegerField(min_value=1, max_value=20, required=False)
    num_ctx = serializers.IntegerField(min_value=512, max_value=131072, required=False)

    def validate_question(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("Ask something first.")
        return value
