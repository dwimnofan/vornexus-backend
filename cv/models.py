# jobs/models.py
from django.db import models
from django.contrib.auth.models import User

class CV(models.Model):
    id = models.AutoField(primary_key=True)
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cvs')
    file_url = models.URLField()
    parsed_text = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"CV {self.id} - {self.user.username}"
