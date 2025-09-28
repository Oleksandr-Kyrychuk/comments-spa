from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import Comment
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging
from .tasks import save_comment

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Comment)
def comment_created(sender, instance, created, **kwargs):
    if created:
        try:
            with transaction.atomic():
                channel_layer = get_channel_layer()
                # Fix: Serialize here if keeping this, or remove entirely since task does it
                serialized_comment = CommentSerializer(instance).data  # Add this
                async_to_sync(channel_layer.group_send)(
                    'comments_group',
                    {
                        'type': 'new_comment',
                        'comment': serialized_comment  # Change to 'comment'
                    }
                )
                logger.info(f"Signal sent for new comment ID: {instance.id}")
        except Exception as e:
            logger.error(f"Error in comment_created signal for comment ID {instance.id}: {str(e)}")