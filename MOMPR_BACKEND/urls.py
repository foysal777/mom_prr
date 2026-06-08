
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from drf_spectacular.renderers import JSONRenderer

from django.views.generic.base import RedirectView

favicon_view = RedirectView.as_view(url='/static/favicon.ico', permanent=True)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('accounts.urls')),
    path('movie_and_series/', include('movie_series.urls')),
    path('favicon.ico', favicon_view),
    path('payment/', include('payment_app.urls')),
    path('notification/', include('notification.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += [
        path('schema/', SpectacularAPIView.as_view(renderer_classes=[JSONRenderer]), name='schema'),
        path('swagger/', SpectacularSwaggerView.as_view(), name='swagger-ui'),
        path('docs/', SpectacularRedocView.as_view(), name='swagger-ui'),

    ]

urlpatterns += static(
    settings.STATIC_URL, document_root=settings.STATIC_ROOT
)