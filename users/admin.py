from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.formats import date_format
from django import forms


User = get_user_model()


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = "__all__"
        widgets = {
            'username': forms.TextInput(attrs={'class': 'mc-input', 'placeholder': 'Логин'}),
            'email': forms.EmailInput(attrs={'class': 'mc-input', 'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'class': 'mc-input', 'placeholder': 'Имя'}),
            'last_name': forms.TextInput(attrs={'class': 'mc-input', 'placeholder': 'Фамилия'}),
            'department': forms.Select(attrs={'class': 'mc-input'}),
            'description': forms.Textarea(attrs={'class': 'mc-textarea', 'rows': 4, 'placeholder': 'Описание'}),
        }


class InAdminGroupFilter(admin.SimpleListFilter):
    title = "В группе admin"
    parameter_name = "in_admin_group"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Да"),
            ("no", "Нет"),
        )

    def queryset(self, request, queryset):
        try:
            admin_group = Group.objects.get(name="admin")
        except Group.DoesNotExist:
            admin_group = None

        val = self.value()
        if not val:
            return queryset

        if not admin_group:
            # Группа отсутствует — «да» даст пусто, «нет» — весь список
            return queryset.none() if val == "yes" else queryset

        if val == "yes":
            return queryset.filter(groups=admin_group)
        if val == "no":
            return queryset.exclude(groups=admin_group)
        return queryset


class StaffAccessFilter(admin.SimpleListFilter):
    title = "Доступ в админку"
    parameter_name = "staff_access"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Да (is_staff=True)"),
            ("no", "Нет"),
        )

    def queryset(self, request, queryset):
        val = self.value()
        if val == "yes":
            return queryset.filter(is_staff=True)
        if val == "no":
            return queryset.filter(is_staff=False)
        return queryset


@admin.register(User)
class UserAdmin(DjangoUserAdmin):

    list_display = ("card",)
    list_display_links = ("card",)
    list_per_page = 30

    list_filter = (
        "is_active",
        "is_superuser",
        StaffAccessFilter,   # доступ в админку (is_staff)
        InAdminGroupFilter,  # членство в группе admin
        "department",
    )
    search_fields = ("username", "first_name", "last_name", "email", "department__name")

    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Организация", {"fields": ("department",)}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        (None, {"fields": ("department",)}),
    )

    def get_urls(self):
        urls = super().get_urls()
        my = [
            path(
                "<int:pk>/toggle-active/",
                self.admin_site.admin_view(self.toggle_active),
                name="users_user_toggle_active",
            ),
            path(
                "<int:pk>/toggle-admin/",
                self.admin_site.admin_view(self.toggle_admin),
                name="users_user_toggle_admin",
            ),
        ]
        return my + urls

    def _back(self, request, fallback_name):
        return HttpResponseRedirect(request.META.get("HTTP_REFERER") or reverse(fallback_name))

    # ---------------------- Быстрые действия ----------------------
    def toggle_active(self, request, pk):
        obj = User.objects.filter(pk=pk).first()
        if not obj:
            messages.error(request, "Пользователь не найден.")
            return self._back(request, "admin:users_user_changelist")
        if not self.has_change_permission(request, obj):
            messages.error(request, "Недостаточно прав для изменения пользователя.")
            return self._back(request, "admin:users_user_changelist")

        obj.is_active = not obj.is_active
        obj.save(update_fields=["is_active"])
        messages.success(request, f'Пользователь {"активирован" if obj.is_active else "заблокирован"}.')
        return self._back(request, "admin:users_user_changelist")

    def toggle_admin(self, request, pk):
        obj = User.objects.filter(pk=pk).first()
        if not obj:
            messages.error(request, "Пользователь не найден.")
            return self._back(request, "admin:users_user_changelist")
        if not self.has_change_permission(request, obj):
            messages.error(request, "Недостаточно прав для изменения пользователя.")
            return self._back(request, "admin:users_user_changelist")

        admin_group, _ = Group.objects.get_or_create(name="admin")

        if obj.groups.filter(id=admin_group.id).exists():
            # Снять 'admin'
            obj.groups.remove(admin_group)
            if not obj.is_superuser and obj.is_staff:
                obj.is_staff = False
                obj.save(update_fields=["is_staff"])
            messages.success(request, 'Группа "admin" снята, доступ в админку отключён.')
        else:
            # Выдать 'admin' + включить доступ в админку
            obj.groups.add(admin_group)
            if not obj.is_staff:
                obj.is_staff = True
                obj.save(update_fields=["is_staff"])
            messages.success(request, 'Группа "admin" выдана, доступ в админку включён.')

        return self._back(request, "admin:users_user_changelist")

    def card(self, obj: User):
        full_name = obj.get_full_name() or obj.username or f"id:{obj.pk}"
        dept_name = getattr(getattr(obj, "department", None), "name", "—")
        groups = ", ".join(obj.groups.values_list("name", flat=True)) or "—"

        chip_active = format_html('<span class="mc-chip {}">Активен</span>', "mc-chip--ok" if obj.is_active else "")
        chip_staff = format_html('<span class="mc-chip {}">Staff</span>', "mc-chip--warn" if obj.is_staff else "")
        chip_super = format_html('<span class="mc-chip {}">Superuser</span>',
                                 "mc-chip--danger" if obj.is_superuser else "")

        return format_html(
            '''
            <div class="mc-card">
              <div class="mc-head">
                <span class="mc-id">#{id}</span>
                <h2 class="mc-title">{name}</h2>
              </div>

              <div class="mc-chips">{chip_active} {chip_staff} {chip_super}</div>

              <div class="mc-grid">
                <div class="mc-box"><div class="mc-label">Логин</div><p class="mc-val">{username}</p></div>
                <div class="mc-box"><div class="mc-label">Email</div><p class="mc-val">{email}</p></div>
                <div class="mc-box"><div class="mc-label">Подразделение</div><p class="mc-val">{department}</p></div>
                <div class="mc-box"><div class="mc-label">Группы</div><p class="mc-val">{groups}</p></div>
              </div>

              <div class="mc-meta">
                <div>Последний вход: {last_login}</div><div>Создан: {date_joined}</div>
              </div>
            </div>
            ''',
            id=obj.pk, name=full_name, username=(obj.username or "—"),
            email=(obj.email or "—"), department=dept_name, groups=groups,
            chip_active=chip_active, chip_staff=chip_staff, chip_super=chip_super,
            last_login=(date_format(obj.last_login, "j E Y в H:i") if getattr(obj, "last_login", None) else "—"),
            date_joined=(date_format(obj.date_joined, "j E Y в H:i") if getattr(obj, "date_joined", None) else "—"),
        )

    card.short_description = "Пользователь"

    class Media:
        css = {"all": ("users/admin-card.css",)}
