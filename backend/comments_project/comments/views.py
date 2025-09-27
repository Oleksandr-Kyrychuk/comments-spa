from rest_framework import generics, viewsets
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
from .tasks import save_comment
from django.core.cache import cache
from django.db import transaction

logger = logging.getLogger(__name__)

class CommentPagination(PageNumberPagination):
    page_size = 25

class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    pagination_class = CommentPagination
    permission_classes = [AllowAny]
    authentication_classes = [JWTAuthentication]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['user__username', 'user__email', 'created_at']
    ordering_fields = ['user__username', 'user__email', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        ordering = self.request.query_params.get('ordering', '-created_at')
        queryset = Comment.objects.filter(parent__isnull=True).select_related('user').order_by(ordering)
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

class CommentListCreateView(generics.ListCreateAPIView):
    queryset = Comment.objects.filter(parent__isnull=True).select_related('user')
    serializer_class = CommentSerializer
    permission_classes = [AllowAny]
    authentication_classes = [JWTAuthentication]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['user__username', 'user__email', 'created_at']
    ordering_fields = ['user__username', 'user__email', 'created_at']
    pagination_class = CommentPagination

    def list(self, request, *args, **kwargs):
        logger.info("Accessing CommentListCreateView.list")
        try:
            # Clear cache for comment list to ensure fresh data
            cache_key = f"comment_list_{request.query_params.get('page', '1')}_{request.query_params.get('ordering', '-created_at')}"
            cache.delete(cache_key)
            logger.info(f"Cleared cache for key: {cache_key}")

            response = super().list(request, *args, **kwargs)
            logger.info("CommentListCreateView.list successful")
            cache.set(cache_key, response.data, timeout=60 * 15)
            return response
        except Exception as e:
            logger.error(f"Error in CommentListCreateView.list: {str(e)}")
            raise

    def create(self, request, *args, **kwargs):
        logger.info(f"Received data: {request.data}")
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    instance = serializer.save()
                    logger.info(f"Comment saved with id: {instance.id}")

                    # Викликаємо Celery таск для WebSocket
                    save_comment.delay(instance.id)

                # Очищаємо весь кеш після створення коментаря
                cache.clear()
                logger.info("Cache cleared after comment creation")

                # Повертаємо відповідь
                parent_id = instance.parent.id if instance.parent else None
                response_data = {
                    'id': instance.id,
                    'user': serializer.validated_data['user'],
                    'text': serializer.validated_data['text'],
                    'parent': parent_id,
                    'file': str(serializer.validated_data.get('file')) if serializer.validated_data.get('file') else None,
                    'created_at': instance.created_at,
                    'replies': [],
                    'parent_username': instance.parent.user.username if instance.parent else ''
                }
                return Response(
                    {
                        "message": "Comment saved successfully",
                        "data": response_data
                    },
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                logger.error(f"Error creating comment: {str(e)}")
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.error(f"Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PreviewView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        logger.info("Accessing PreviewView.post")
        text = request.data.get('text', '')
        ALLOWED_TAGS = ['a', 'code', 'i', 'strong']
        ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}
        cleaned_text = bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
        return Response({'preview': cleaned_text})
