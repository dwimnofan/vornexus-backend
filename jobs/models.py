from django.db import models

class Job(models.Model):
    category = models.CharField(max_length=30, blank=True, null=True)
    job_hash = models.CharField(max_length=32, unique=True)  # MD5 hash dari URL
    job_title = models.CharField(max_length=255)
    company_logo = models.URLField(blank=True, null=True)
    company_industry = models.CharField(max_length=255, blank=True, null=True)
    company_desc = models.TextField(blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    company_employee_size = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    url = models.URLField(unique=True)
    job_type = models.CharField(max_length=100, blank=True, null=True)
    industry = models.CharField(max_length=255, blank=True, null=True)
    job_description = models.TextField(blank=True, null=True)
    experience_level = models.CharField(max_length=100, blank=True, null=True)
    education_level = models.CharField(max_length=100, blank=True, null=True)
    salary = models.CharField(max_length=100, blank=True, null=True)
    skills_required = models.TextField(blank=True, null=True)
    date_posted = models.TextField(blank=True, null=True)
    uploaded_to_vector_db = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.job_title} at {self.company_name}"