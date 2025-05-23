from django.db import models
from django.utils.text import slugify

class JobCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Job Categories"

class JobSource(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class Job(models.Model):
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField()
    url = models.URLField(unique=True)
    salary = models.CharField(max_length=100, null=True, blank=True)
    posted_date = models.DateField(null=True, blank=True)
    category = models.ForeignKey(JobCategory, on_delete=models.CASCADE, related_name='jobs')
    source = models.ForeignKey(JobSource, on_delete=models.CASCADE, related_name='jobs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} at {self.company}"
    
    class Meta:
        ordering = ['-created_at']
