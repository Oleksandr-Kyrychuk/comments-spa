from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework_simplejwt.authentication import JWTAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from .models import Comment
from .serializers import CommentSerializer

class CommentListCreateView(generics.ListCreateAPIView):
    queryset = Comment.objects.filter(parent__isnull=True)  # Тільки кореневі коментарі
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]  # JWT для POST
    authentication_classes = [JWTAuthentication]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user_name', 'email', 'created_at']
    ordering_fields = ['user_name', 'email', 'created_at']
    pagination_class = 'rest_framework.pagination.PageNumberPagination'