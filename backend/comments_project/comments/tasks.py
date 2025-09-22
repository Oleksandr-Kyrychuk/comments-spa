from celery import shared_task
from .models import Comment
from .serializers import CommentSerializer
import logging

logger = logging.getLogger(__name__)

@shared_task
def save_comment(data):
    logger.info(f"Task received data: {data}")
    serializer = CommentSerializer(data=data)
    if serializer.is_valid():
        instance = serializer.save()
        logger.info(f"Saved comment ID: {instance.id}")
        return {
            "id": instance.id,
            "created_at": instance.created_at.isoformat(),
            "message": "Comment saved successfully"
        }
    else:
        logger.error(f"Task serializer errors: {serializer.errors}")
        raise ValueError(f"Invalid data in task: {serializer.errors}")