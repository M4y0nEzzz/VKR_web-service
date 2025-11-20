from django.contrib import admin
from .models import Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "events_count",
    )

    search_fields = (
        "name",
    )

    list_filter = (
        ### ------------ ###
    )

    readonly_fields = (
        ### ------------ ###
    )

    def events_count(self, obj):
        return obj.event_set.count()
    events_count.short_description = "Количество мероприятий"
