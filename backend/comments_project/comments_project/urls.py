from captcha.views import captcha_refresh
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def csrf_cookie(request):
    return HttpResponse(status=200)

def health_check(request):
    return HttpResponse("OK", status=200)

urlpatterns = [
    path('', health_check, name='health-check'),  # Додаємо простий маршрут для healthcheck
    path('admin/', admin.site.urls),
    path('csrf-cookie/', csrf_cookie, name='csrf_cookie'),
    path('api/', include('comments.urls')),
    path('captcha/', include('captcha.urls')),
    path('captcha/refresh/', captcha_refresh, name='captcha-refresh-get'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)