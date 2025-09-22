# backend/comments/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Comment
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .serializers import CommentSerializer

@receiver(post_save, sender=Comment)
def comment_saved(sender, instance, created, **kwargs):
    if created:
        print(f"Event: New comment by {instance.user_name}: {instance.text[:50]}")
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            "comments_group",
            {
                "type": "new_comment",
                "comment_id": instance.id
            }
        )