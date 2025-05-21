# jobs/models.py
from django.db import models
from django.contrib.auth.models import User 

class JobRecommendation(models.Model):
    id = models.AutoField(primary_key=True)
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    # cv = models.ForeignKey('cv.CV', on_delete=models.CASCADE, related_name='recommendations')
    job_id = models.CharField(max_length=100)
    title = models.CharField(max_length=255, blank=True, null=True)
    company_logo = models.URLField(blank=True, null=True)
    company = models.CharField(max_length=255, blank=True, null=True)
    company_desc = models.TextField(blank=True, null=True)
    company_industry = models.CharField(max_length=255, blank=True, null=True)
    company_employee_size = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    match_score = models.IntegerField(blank=True, null=True)
    matched_skills = models.JSONField(default=list, blank=True)
    required_skills = models.JSONField(default=list, blank=True)
    job_description = models.TextField()
    apply_link = models.URLField(blank=True, null=True)
    recommended_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recommendation for {self.user.username} - {self.title} at {self.company} (score: {self.match_score})"
