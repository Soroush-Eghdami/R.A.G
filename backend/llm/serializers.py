"""Serializers that document the shape of the ``llm`` endpoints."""

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
    chat_base_url = serializers.CharField()
    embedding_base_url = serializers.CharField()


class LlamaCppHealthSerializer(serializers.Serializer):
    reachable = serializers.BooleanField()
    base_url = serializers.CharField()
    error = serializers.CharField(allow_null=True)


class DatabaseHealthSerializer(serializers.Serializer):
    ok = serializers.BooleanField()


class HealthResponseSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["ok", "degraded"])
    chat = LlamaCppHealthSerializer()
    embedding = LlamaCppHealthSerializer()
    database = DatabaseHealthSerializer()


class ErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()
    code = serializers.CharField()


class AppSettingsSerializer(serializers.ModelSerializer):
    # Deployment settings are read-only here.
    llama_cpp_chat_base_url = serializers.SerializerMethodField()
    llama_cpp_embedding_base_url = serializers.SerializerMethodField()
    max_num_ctx = serializers.SerializerMethodField()

    class Meta:
        model = AppSettings
        fields = [
            "default_chat_model",
            "default_embedding_model",
            "top_k",
            "temperature",
            "num_ctx",
            "llama_cpp_chat_base_url",
            "llama_cpp_embedding_base_url",
            "max_num_ctx",
            "updated_at",
        ]
        read_only_fields = [
            "llama_cpp_chat_base_url",
            "llama_cpp_embedding_base_url",
            "max_num_ctx",
            "updated_at",
        ]

    def get_llama_cpp_chat_base_url(self, obj: AppSettings) -> str:
        from django.conf import settings

        return settings.LLAMA_CPP_CHAT_BASE_URL

    def get_llama_cpp_embedding_base_url(self, obj: AppSettings) -> str:
        from django.conf import settings

        return settings.LLAMA_CPP_EMBEDDING_BASE_URL

    def get_max_num_ctx(self, obj: AppSettings) -> int:
        from django.conf import settings

        return settings.LLAMA_CPP_CONTEXT_SIZE

    def validate_top_k(self, value: int) -> int:
        if not 1 <= value <= 20:
            raise serializers.ValidationError("Between 1 and 20.")
        return value

    def validate_temperature(self, value: float) -> float:
        if not 0 <= value <= 2:
            raise serializers.ValidationError("Between 0 and 2.")
        return value

    def validate_num_ctx(self, value: int) -> int:
        from django.conf import settings

        if not 512 <= value <= settings.LLAMA_CPP_CONTEXT_SIZE:
            raise serializers.ValidationError(
                f"Between 512 and {settings.LLAMA_CPP_CONTEXT_SIZE}."
            )
        return value
