import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'comments_project.settings')

# Ініціалізуємо Django ASGI додаток
django_asgi_app = get_asgi_application()

# Відкладаємо імпорт routing до моменту, коли він буде потрібен
def get_application():
    from comments import routing
    return ProtocolTypeRouter({
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(routing.websocket_urlpatterns)
        ),
    })

application = get_application()