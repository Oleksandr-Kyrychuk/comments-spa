"""
ASGI config for comments_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'comments_project.settings')

from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import comments.routing  # Імпорт роутингу з comments
from channels.sessions import SessionMiddlewareStack


application = ProtocolTypeRouter({
    "http": SessionMiddlewareStack(django_asgi_app),
    "websocket": AuthMiddlewareStack(
        URLRouter(comments.routing.websocket_urlpatterns)
    ),
})