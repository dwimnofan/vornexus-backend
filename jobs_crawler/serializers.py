from rest_framework import serializers
from .models import JobCategory, JobSource, Job

class JobCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobCategory
        fields = '__all__'

class JobSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobSource
        fields = '__all__'

class JobSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    source_name = serializers.CharField(source='source.name', read_only=True)
    
    class Meta:
        model = Job
        fields = '__all__'
