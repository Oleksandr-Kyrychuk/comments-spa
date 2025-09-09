from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Comment

@receiver(post_save, sender=Comment)
def comment_saved(sender, instance, created, **kwargs):
    if created:
        print(f"Event: New comment by {instance.user.username}: {instance.text[:50]}")
