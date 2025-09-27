import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'comments_project.settings')

# Django ASGI додаток
django_asgi_app = get_asgi_application()

# Routing відкладаємо
try:
    from comments import routing
    websocket_patterns = routing.websocket_urlpatterns
except ImportError:
    websocket_patterns = []

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_patterns)
    ),
})
