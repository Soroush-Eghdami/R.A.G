"""Conversations and messages."""

from __future__ import annotations

import uuid

from django.db import models
from kb.models import KnowledgeBase


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    knowledge_base = models.ForeignKey(
        KnowledgeBase,
        related_name="conversations",
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=200, blank=True)
    chat_model = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.title or str(self.id)


class Message(models.Model):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"

    id = models.BigAutoField(primary_key=True)
    conversation = models.ForeignKey(
        Conversation,
        related_name="messages",
        on_delete=models.CASCADE,
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    content = models.TextField()
    sources = models.JSONField(default=list, blank=True)
    model_used = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.role}: {self.content[:40]}"
