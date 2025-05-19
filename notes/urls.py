from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, 
    LoginView, 
    LogoutView, 
    UserProfileView,
    UserProfileDetailView,
    NoteViewSet
)

# Set up the router for the notes viewset
router = DefaultRouter()
router.register(r'notes', NoteViewSet, basename='note')

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    
    # User profile endpoints
    path('users/me/', UserProfileView.as_view(), name='user-profile'),
    path('users/profile/', UserProfileDetailView.as_view(), name='user-profile-detail'),
    
    # Notes endpoints (using the router)
    path('', include(router.urls)),
]
