    # apps/jobmatching/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import JobRecommendation
from .serializers import JobRecommendationSerializer
from django.contrib.auth import get_user_model

class JobRecommendationView(APIView):

    def get(self, request):
        User = get_user_model()
        try:
            user = User.objects.get(username='ismail')  
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        limit = request.query_params.get('limit')
        recommendations = JobRecommendation.objects.filter(user=user)
        print("Count recommendations:", recommendations.count())

        if limit is not None:
            try:
                limit = int(limit)
                recommendations = recommendations[:limit]
            except ValueError:
                return Response({"error": "Limit must be an integer"}, status=400)  

        if not recommendations.exists():
            return Response({"message": "No job recommendations for this user"}, status=404)

        serializer = JobRecommendationSerializer(recommendations, many=True)
        return Response(serializer.data)

    
    # permission_classes = [IsAuthenticated]

    # def get(self, request):
    #     user = request.user
    #     if not user.is_authenticated:
    #         return Response({"message": "User is not authenticated"}, status=403)

    #     limit = request.query_params.get('limit')
    #     recommendations = JobRecommendation.objects.filter(user=user)
    #     if limit is not None:
            # try:
            #     limit = int(limit)
            #     recommendations = recommendations[:limit]
            # except ValueError:
            #     return Response({"error": "Limit must be an integer"}, status=400)  
        
    #     if not recommendations.exists():
    #         return Response({"message": "No job recommendations for this user"}, status=404)

    #     serializer = JobRecommendationSerializer(recommendations, many=True)
    #     return Response(serializer.data)