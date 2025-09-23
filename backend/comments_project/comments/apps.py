from django.apps import AppConfig

class CommentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'comments'

    # def ready(self):
    #     from comments_project.comments import signals  # signals для Events