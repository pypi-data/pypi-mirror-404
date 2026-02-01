from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser

class BaseAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]