from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Assessment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assessments")
    # Inputs
    math = models.FloatField()
    science = models.FloatField()
    english = models.FloatField()
    arts = models.FloatField()
    coding = models.FloatField()
    design = models.FloatField()
    leadership = models.FloatField()
    communication = models.FloatField()
    interests = models.TextField(blank=True)

    # Store JSON as TEXT (since SQLite JSONField isn’t available)
    top3 = models.TextField()  # JSON string: e.g. '[{"career":"...", "prob":0.83}, ...]'

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} · {self.created_at:%Y-%m-%d %H:%M}"
# in Assessment model
import json
@property
def top3_list(self):
    try:
        return json.loads(self.top3) if self.top3 else []
    except Exception:
        return []
