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
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.utils.decorators import method_decorator

logger = logging.getLogger(__name__)

class CommentPagination(PageNumberPagination):
    page_size = 25

class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    pagination_class = CommentPagination
    permission_classes = [IsAuthenticatedOrReadOnly]
    authentication_classes = [JWTAuthentication]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['user__username', 'user__email', 'created_at']
    ordering_fields = ['user__username', 'user__email', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = Comment.objects.filter(parent__isnull=True).select_related('user').order_by('-created_at')
        ordering = self.request.query_params.get('ordering')
        if ordering in ['created_at', '-created_at']:
            queryset = queryset.order_by(ordering)
        return queryset

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
            response = super().list(request, *args, **kwargs)
            logger.info("CommentListCreateView.list successful")
            return response
        except Exception as e:
            logger.error(f"Error in CommentListCreateView.list: {str(e)}")
            raise

    def create(self, request, *args, **kwargs):
        logger.info(f"Received data: {request.data}")
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            logger.info(f"Validated data: {serializer.validated_data}")
            save_comment.delay(serializer.validated_data)
            return Response(
                {
                    "message": "Comment accepted for processing",
                    "data": serializer.validated_data
                },
                status=status.HTTP_202_ACCEPTED
            )

    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        cache_key = f"comment_list_{request.query_params.get('page', '1')}_{request.query_params.get('ordering', '-created_at')}"
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info("Returning cached comment list")
            return Response(cached_data)
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=60 * 15)
        return response

class PreviewView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        logger.info("Accessing PreviewView.post")
        text = request.data.get('text', '')
        ALLOWED_TAGS = ['a', 'code', 'i', 'strong']
        ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}
        cleaned_text = bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
        return Response({'preview': cleaned_text})