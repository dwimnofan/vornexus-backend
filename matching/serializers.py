# apps/jobmatching/serializers.py
from rest_framework import serializers
from .models import JobRecommendation

class JobRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobRecommendation
        fields = [
            'job_id',
            'title',
            'company_logo',
            'company',
            'company_desc',
            'company_industry',
            'company_employee_size',
            'location',
            'match_score',
            'matched_skills',
            'required_skills',
            'job_description',
            'apply_link',
        ]
