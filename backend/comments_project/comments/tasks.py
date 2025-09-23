from celery import shared_task
from .models import Comment, User
from .serializers import CommentSerializer
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


@shared_task
def save_comment(data):
    logger.info(f"Task received data: {data}")
    serializer = CommentSerializer(data=data)
    if serializer.is_valid():
        instance = serializer.save()

        # Серіалізуємо коментар для WebSocket
        serialized_comment = CommentSerializer(instance).data

        # Надсилаємо через WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'comments',
            {
                'type': 'new_comment',
                'comment': serialized_comment,
            }
        )

        return {
            "id": instance.id,
            "created_at": instance.created_at.isoformat(),
            "message": "Comment saved successfully"
        }
    else:
        logger.error(f"Task serializer errors: {serializer.errors}")
        raise ValueError(f"Invalid data in task: {serializer.errors}")