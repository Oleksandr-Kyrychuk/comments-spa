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
from .tasks import save_comment
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page


logger = logging.getLogger(__name__)
from rest_framework import viewsets
from .models import Comment
from .serializers import CommentSerializer
from rest_framework.pagination import PageNumberPagination

class CommentPagination(PageNumberPagination):
    page_size = 25

class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    pagination_class = CommentPagination

    def get_queryset(self):
        # Повертаємо лише кореневі коментарі (parent=null)
        queryset = Comment.objects.filter(parent__isnull=True).order_by('-created_at')
        ordering = self.request.query_params.get('ordering')
        if ordering:
            queryset = queryset.order_by(ordering)
        return queryset


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
        return super().list(request, *args, **kwargs)


    
class PreviewView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        text = request.data.get('text', '')
        ALLOWED_TAGS = ['a', 'code', 'i', 'strong']
        ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}
        cleaned_text = bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
        return Response({'preview': cleaned_text})

