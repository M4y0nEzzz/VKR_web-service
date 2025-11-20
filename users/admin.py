from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from django.contrib.auth.models import Group


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('department',)}),
    )
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'department',
        'is_staff',
        'is_superuser',
        'get_groups',
        'events_created_count',
        'events_responsible_count',
    )

    list_filter = (
        'department',
        'is_staff',
        'is_superuser',
        'groups',
    )

    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
        'department__name',
    )

    autocomplete_fields = (
        'department',
    )

    readonly_fields = (
        'last_login',
        'date_joined',
    )

    def events_created_count(self, obj):
        return obj.events_created.count()
    events_created_count.short_description = "Создал мероприятий"

    def events_responsible_count(self, obj):
        return obj.events_responsible.count()
    events_responsible_count.short_description = "Ответственный в"

    def get_groups(self, obj):
        return ", ".join(
            [group.name for group in obj.groups.all()])
    get_groups.short_description = 'Группы'
