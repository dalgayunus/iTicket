from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
   openapi.Info(
        title="iTicket API",
        default_version='v1',
        description="API documentation for iTicket project",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

def return_all_links(request):
    return HttpResponse('<a href="/api/events/">Events</a> <a href="/auth/login/">Login</a> <a href="/auth/register/">Register</a>')

urlpatterns = [
    path('', return_all_links),
    path('admin/', admin.site.urls),
    path('api/', include('event.urls')),
    path('auth/', include('user.urls')),
    path('swagger(<format>\.json|\.yaml)', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)