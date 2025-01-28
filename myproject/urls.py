from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('testapp/', include('testapp.urls')),
    # ... your other URLs
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 