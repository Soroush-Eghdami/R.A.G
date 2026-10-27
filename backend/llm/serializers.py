"""Serializers that document the shape of the ``llm`` endpoints."""

from rest_framework import serializers


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
