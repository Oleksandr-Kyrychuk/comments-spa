from celery import shared_task
from .models import Comment
from .serializers import CommentSerializer
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

@shared_task
def save_comment(comment_id):
    """
    Celery таск для відправки вже збереженого коментаря через WebSocket.
    """
    try:
        # отримуємо коментар з бази
        instance = Comment.objects.get(id=comment_id)

        # серіалізуємо для WebSocket
        serialized_comment = CommentSerializer(instance, context={'request': None}).data

        # надсилаємо через WebSocket
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
        logger.error(f"Error in send_comment_ws task: {str(e)}")
        raise
