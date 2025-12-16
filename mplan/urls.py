from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # Пользовательский интерфейс мероприятий
    path("events/", include("events.urls")),
]
