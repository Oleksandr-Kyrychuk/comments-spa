from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework_simplejwt.authentication import JWTAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from .models import Comment
from .serializers import CommentSerializer
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.filters import OrderingFilter
import bleach
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


class CommentListCreateView(generics.ListCreateAPIView):
    queryset = Comment.objects.filter(parent__isnull=True)
    serializer_class = CommentSerializer
    permission_classes = [AllowAny]
    authentication_classes = [JWTAuthentication]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['user_name', 'email', 'created_at']
    ordering_fields = ['user_name', 'email', 'created_at']
    pagination_class = PageNumberPagination

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class PreviewView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        text = request.data.get('text', '')
        ALLOWED_TAGS = ['a', 'code', 'i', 'strong']
        ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}
        cleaned_text = bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
        return Response({'preview': cleaned_text})

