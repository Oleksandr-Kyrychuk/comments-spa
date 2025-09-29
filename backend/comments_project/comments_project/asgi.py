import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from comments import routing  # Імпорт тут, не в функції

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'comments_project.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
    URLRouter(routing.websocket_urlpatterns)

    ),
})