from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JobCategoryViewSet, JobSourceViewSet, JobViewSet, TriggerCrawlView

router = DefaultRouter()
router.register(r'categories', JobCategoryViewSet)
router.register(r'sources', JobSourceViewSet)
router.register(r'jobs', JobViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('trigger-crawl/', TriggerCrawlView.as_view(), name='trigger-crawl'),
]
