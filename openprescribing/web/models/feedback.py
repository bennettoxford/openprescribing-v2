from django.db import models
from django.utils import timezone


class Feedback(models.Model):
    timestamp = models.DateTimeField(default=timezone.now)
    thumbs_up = models.BooleanField()
    text = models.CharField()
