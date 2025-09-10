from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework_simplejwt.authentication import JWTAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from .models import Comment
from .serializers import CommentSerializer
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

class CommentListCreateView(generics.ListCreateAPIView):
    queryset = Comment.objects.filter(parent__isnull=True)  # Тільки кореневі коментарі
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]  # JWT для POST
    authentication_classes = [JWTAuthentication]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user_name', 'email', 'created_at']
    ordering_fields = ['user_name', 'email', 'created_at']
    pagination_class = PageNumberPagination

class PreviewView(APIView):
    def post(self, request):
        text = request.data.get('text', '')
        ALLOWED_TAGS = ['a', 'code', 'i', 'strong']
        ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}
        cleaned_text = bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
        return Response({'preview': cleaned_text})

