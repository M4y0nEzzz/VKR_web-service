from django.contrib import admin
from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "events_count",
    )

    search_fields = (
        "name",
    )

    def events_count(self, obj):
        return obj.event_set.count()
    events_count.short_description = "Количество мероприятий"
