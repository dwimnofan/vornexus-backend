# jobs/models.py
from django.db import models

class Job(models.Model):
    JOB_TYPE_CHOICES = [
        ('fulltime', 'Full-time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('freelance', 'Freelance'),
        ('other', 'Other'),
    ]

    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    salary_range = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField()
    YoE = models.PositiveIntegerField(help_text="Years of Experience required")
    type = models.CharField(max_length=50, choices=JOB_TYPE_CHOICES)
    source_url = models.URLField()
    scraped_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} at {self.company}"
