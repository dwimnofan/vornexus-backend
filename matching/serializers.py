# apps/jobmatching/serializers.py
from rest_framework import serializers
from .models import JobRecommendation
from jobs.models import Job
# from users.models import User
# from cv.models import CV  # Sesuaikan path modelmu

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'title', 'company', 'location', 'salary_range', 'description', 'YoE', 'type', 'source_url']


class JobRecommendationSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)

    class Meta:
        model = JobRecommendation
        fields = ['id', 'job', 'score_match', 'recommended_at']
