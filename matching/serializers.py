from rest_framework import serializers
from jobs.models import Job
from matching.models import JobRecommendation
import ast

class JobSerializer(serializers.ModelSerializer):
    required_skills = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'job_hash',  # misal sebagai job_id
            'job_title',
            'company_logo',
            'company_name',
            'company_desc',
            'company_industry',
            'company_employee_size',
            'location',
            'required_skills',
            'job_description',
            'url',
        ]

    def get_required_skills(self, obj):
        if obj.skills_required:
            try:
                # Parse string Python list ke list Python asli
                skills_list = ast.literal_eval(obj.skills_required)
                # pastikan hasilnya list dan semua element adalah string
                if isinstance(skills_list, list):
                    return [str(skill).strip() for skill in skills_list]
                else:
                    return []
            except Exception:
                # fallback kalau parsing gagal, kembalikan string utuh
                return [obj.skills_required]
        return []

class JobRecommendationSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)
    match_score = serializers.FloatField(source='score')
    matched_skills = serializers.ListField(child=serializers.CharField(), default=[])

    class Meta:
        model = JobRecommendation
        fields = [
            'job',
            'match_score',
            'matched_skills',
        ]