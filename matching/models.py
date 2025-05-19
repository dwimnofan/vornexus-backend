# jobs/models.py
from django.db import models
from django.contrib.auth.models import User 

class JobRecommendation(models.Model):
    id = models.AutoField(primary_key=True)
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    job = models.ForeignKey('jobs.Job', on_delete=models.CASCADE, related_name='recommendations')
    cv = models.ForeignKey('cv.CV', on_delete=models.CASCADE, related_name='recommendations')

    score_match = models.FloatField()
    recommended_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recommendation for {self.user.username} - {self.job.title} (score: {self.score_match})"
