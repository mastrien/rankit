"""Shared abstract base models for Rankit domain apps."""

from django.db import models


class TimestampedModel(models.Model):
    """Abstract model providing automatic creation and update timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
