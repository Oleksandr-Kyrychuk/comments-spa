from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Comment
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging
from .tasks import notify_new_comment

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Comment)
def comment_created(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'comments_group',
            {
                'type': 'new_comment',
                'comment_id': instance.id
            }
        )
        logger.info(f"Signal sent for new comment ID: {instance.id}")


@receiver(post_save, sender=Comment)
def comment_post_save(sender, instance, created, **kwargs):
    if created:
        notify_new_comment.delay(instance.id)