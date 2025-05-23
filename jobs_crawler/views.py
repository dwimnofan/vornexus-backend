from rest_framework import viewsets, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from .models import JobCategory, JobSource, Job
from .serializers import JobCategorySerializer, JobSourceSerializer, JobSerializer
from .tasks import crawl_jobs

class JobCategoryViewSet(viewsets.ModelViewSet):
    queryset = JobCategory.objects.all()
    serializer_class = JobCategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

class JobSourceViewSet(viewsets.ModelViewSet):
    queryset = JobSource.objects.all()
    serializer_class = JobSourceSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

class JobViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'source', 'posted_date']
    search_fields = ['title', 'company', 'description', 'location']
    ordering_fields = ['posted_date', 'created_at']
    ordering = ['-created_at']

class TriggerCrawlView(APIView):
    def post(self, request, format=None):
        source_ids = request.data.get('source_ids', [])
        
        if not source_ids:
            # If no sources specified, crawl all active sources
            sources = JobSource.objects.filter(is_active=True)
        else:
            sources = JobSource.objects.filter(id__in=source_ids, is_active=True)
        
        if not sources.exists():
            return Response(
                {"error": "No active sources found to crawl"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        for source in sources:
            crawl_jobs.delay(source.id)
        
        return Response(
            {"message": f"Crawling initiated for {sources.count()} sources"}, 
            status=status.HTTP_202_ACCEPTED
        )
