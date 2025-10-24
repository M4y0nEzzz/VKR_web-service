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
        'get_groups'
    )

    list_filter = (
        'department',
        'is_staff',
        'is_superuser',
        'groups'
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

    def get_groups(self, obj):
        return ", ".join(
            [group.name for group in obj.groups.all()])
    get_groups.short_description = 'Группы'
