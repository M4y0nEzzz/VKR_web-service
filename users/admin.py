# users/admin.py
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html

User = get_user_model()


# ---------------------- КАСТОМНЫЕ ФИЛЬТРЫ ----------------------

class InAdminGroupFilter(admin.SimpleListFilter):
    """Фильтр: состоит ли пользователь в группе 'admin'."""
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
    """Фильтр: есть ли доступ в админку (is_staff)."""
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
    """
    Карточки пользователей + быстрые действия.
    Никаких 'roles' — только группы и флаги is_staff/is_superuser.
    """

    # Список — одна колонка «карточка»
    list_display = ("card",)
    list_display_links = ("card",)
    list_per_page = 30

    # Фильтры/поиск — убрал сырой 'groups' и добавил понятные фильтры
    list_filter = (
        "is_active",
        "is_superuser",
        StaffAccessFilter,   # доступ в админку (is_staff)
        InAdminGroupFilter,  # членство в группе admin
        "department",
    )
    search_fields = ("username", "first_name", "last_name", "email", "department__name")

    # Поля формы на странице изменения/создания
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Организация", {"fields": ("department",)}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        (None, {"fields": ("department",)}),
    )

    class Media:
        # Переиспользуем стили карточек из событий
        css = {"all": ("events/admin.css",)}

    # ---------------------- Пользовательские URL'ы ----------------------
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
        """
        Выдаёт/снимает группу 'admin' и синхронизирует is_staff.
        - Если добавили в 'admin' → is_staff=True.
        - Если убрали из 'admin' → is_staff=False (кроме superuser).
        """
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
            # Суперпользователей не трогаем: им админка доступна всегда
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

    # ---------------------- Карточка пользователя ----------------------
    def card(self, obj: User):
        edit_url = reverse("admin:users_user_change", args=[obj.pk])
        toggle_active_url = reverse("admin:users_user_toggle_active", args=[obj.pk])
        toggle_admin_url = reverse("admin:users_user_toggle_admin", args=[obj.pk])

        fio = " ".join(filter(None, [obj.last_name, obj.first_name])) or obj.username or "—"
        email = obj.email or "—"
        dep_name = getattr(getattr(obj, "department", None), "name", "—")

        # Бейджи-признаки для наглядности
        badges = []
        if obj.is_superuser:
            badges.append("superuser")
        if obj.is_staff:
            badges.append("staff")
        if obj.groups.filter(name="admin").exists():
            badges.append("admin")
        badges_str = ", ".join(badges) or "—"

        # счётчики (если заданы related_name)
        def _safe_count(qs_name):
            try:
                qs = getattr(obj, qs_name, None)
                return qs.count() if qs is not None else "—"
            except Exception:
                return "—"

        created_cnt = _safe_count("events_created")
        responsible_cnt = _safe_count("events_responsible")

        last_login = obj.last_login.strftime("%d.%m.%Y %H:%M") if obj.last_login else "—"
        joined = obj.date_joined.strftime("%d.%m.%Y %H:%M") if obj.date_joined else "—"

        active_badge = format_html(
            '<span style="display:inline-flex;align-items:center;gap:6px;">'
            '<span style="width:10px;height:10px;border-radius:50%;background:{};display:inline-block;"></span>'
            '{}'
            "</span>",
            "#22c55e" if obj.is_active else "#ef4444",
            "Активен" if obj.is_active else "Заблокирован",
        )

        toolbar = format_html(
            """
            <div class="evt-toolbar">
              <a class="evt-btn" href="{edit}">✏️ Изменить</a>
              <a class="evt-btn" href="{t_active}">{active_action}</a>
              <a class="evt-btn" href="{t_admin}">{admin_action}</a>
            </div>
            """,
            edit=edit_url,
            t_active=toggle_active_url,
            active_action=("🔓 Разблокировать" if not obj.is_active else "🔒 Заблокировать"),
            t_admin=toggle_admin_url,
            admin_action=("➖ Снять admin" if obj.groups.filter(name="admin").exists() else "➕ Выдать admin"),
        )

        headline = format_html(
            '<div class="evt-head">'
            '<span class="evt-title" style="font-size:15px;font-weight:600;">{fio}</span>'
            '<span style="margin-left:auto;">{active}</span>'
            "</div>",
            fio=fio,
            active=active_badge,
        )

        about_html = format_html(
            "<b>Логин:</b> {}<br/><b>Email:</b> {}<br/><b>Подразделение:</b> {}<br/><b>Группы доступа:</b> {}",
            obj.username or "—", email, dep_name, badges_str,
        )

        body = format_html(
            """
            <div class="evt-grid">
              <div><b>ID:</b> {id}</div>
              <div><b>Создано мероприятий:</b> {cr}</div>
              <div><b>Ответственный в мероприятиях:</b> {rs}</div>
              <div><b>Последний вход:</b> {ll}</div>
              <div><b>Добавлен:</b> {dj}</div>
            </div>
            """,
            id=obj.pk,
            cr=created_cnt,
            rs=responsible_cnt,
            ll=last_login,
            dj=joined,
        )

        return format_html(
            '<div class="evt-card">{headline}{toolbar}<div class="evt-desc">{about}</div>{body}</div>',
            headline=headline, toolbar=toolbar, about=about_html, body=body
        )

    card.short_description = "Пользователь"
