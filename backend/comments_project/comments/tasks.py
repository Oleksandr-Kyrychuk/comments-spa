from celery import shared_task
from django.db import transaction
from .models import Comment
from .serializers import CommentSerializer
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

@shared_task
def save_comment(comment_id):
    """
    Celery task для відправки вже збереженого коментаря через WebSocket.
    """
    try:
        # Отримуємо коментар з бази з використанням транзакції
        with transaction.atomic():
            instance = Comment.objects.get(id=comment_id)
            logger.info(f"Retrieved comment ID {comment_id} from database")

        # Серіалізуємо для WebSocket
        serialized_comment = CommentSerializer(instance, context={'request': None}).data
        logger.info(f"Serialized comment ID {comment_id}: {serialized_comment}")

        # Надсилаємо через WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'comments_group',
            {
                'type': 'new_comment',
                'comment': serialized_comment,
            }
        )

        logger.info(f"Comment {comment_id} sent via WebSocket")
        return {"id": instance.id, "message": "Comment sent via WebSocket"}

    except Comment.DoesNotExist:
        logger.error(f"Comment with id {comment_id} does not exist")
        raise
    except Exception as e:
        logger.error(f"Error in save_comment task for comment ID {comment_id}: {str(e)}")
        raise