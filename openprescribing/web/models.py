from django.db import models
from django.utils import timezone


class Feedback(models.Model):
    class Sentiment(models.TextChoices):
        THUMBS_UP = "up", "Thumbs up"
        THUMBS_DOWN = "down", "Thumbs down"

    sentiment = models.CharField(max_length=10, choices=Sentiment.choices)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
