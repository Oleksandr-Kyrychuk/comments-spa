from celery import shared_task
from .models import Comment
from .serializers import CommentSerializer

@shared_task
def save_comment(data):
    serializer = CommentSerializer(data=data)
    if serializer.is_valid():
        serializer.save()

