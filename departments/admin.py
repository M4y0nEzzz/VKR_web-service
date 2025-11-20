from django.contrib import admin
from .models import Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "users_count",
        "events_count",
    )

    search_fields = (
        "name",
    )

    def users_count(self, obj):
        return obj.user_set.count()
    users_count.short_description = "Пользователи"

    def events_count(self, obj):
        return obj.event_set.count()
    events_count.short_description = "Мероприятия"
