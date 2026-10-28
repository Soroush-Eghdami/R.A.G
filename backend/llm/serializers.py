"""Serializers that document the shape of the ``llm`` endpoints."""

from django.conf import settings
from rest_framework import serializers

from .models import AppSettings


class ModelSerializer(serializers.Serializer):
    name = serializers.CharField()
    kind = serializers.ChoiceField(choices=["chat", "embedding"])
    capabilities = serializers.ListField(child=serializers.CharField())
    size_bytes = serializers.IntegerField()
    parameter_size = serializers.CharField(allow_blank=True)
    quantization = serializers.CharField(allow_blank=True)
    family = serializers.CharField(allow_blank=True)
    context_length = serializers.IntegerField(allow_null=True)
    is_cloud = serializers.BooleanField()


class ModelsResponseSerializer(serializers.Serializer):
    chat = ModelSerializer(many=True)
    embedding = ModelSerializer(many=True)
    cloud_hidden = serializers.IntegerField(
        help_text="Cloud models hidden because SHOW_CLOUD_MODELS is false."
    )
    base_url = serializers.CharField()


class OllamaHealthSerializer(serializers.Serializer):
    reachable = serializers.BooleanField()
    version = serializers.CharField(allow_null=True)
    base_url = serializers.CharField()
    error = serializers.CharField(allow_null=True)


class DatabaseHealthSerializer(serializers.Serializer):
    ok = serializers.BooleanField()


class HealthResponseSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["ok", "degraded"])
    ollama = OllamaHealthSerializer()
    database = DatabaseHealthSerializer()


class ErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()
    code = serializers.CharField()


class AppSettingsSerializer(serializers.ModelSerializer):
    # Deployment config, so it stays read-only here.
    ollama_base_url = serializers.SerializerMethodField()

    class Meta:
        model = AppSettings
        fields = [
            "default_chat_model",
            "default_embedding_model",
            "top_k",
            "temperature",
            "num_ctx",
            "ollama_base_url",
            "updated_at",
        ]
        read_only_fields = ["ollama_base_url", "updated_at"]

    def get_ollama_base_url(self, obj: AppSettings) -> str:
        return settings.OLLAMA_BASE_URL

    def validate_top_k(self, value: int) -> int:
        if not 1 <= value <= 20:
            raise serializers.ValidationError("Between 1 and 20.")
        return value

    def validate_temperature(self, value: float) -> float:
        if not 0 <= value <= 2:
            raise serializers.ValidationError("Between 0 and 2.")
        return value

    def validate_num_ctx(self, value: int) -> int:
        if not 512 <= value <= 131072:
            raise serializers.ValidationError("Between 512 and 131072.")
        return value
