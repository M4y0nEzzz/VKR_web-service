# departments/admin.py
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.text import Truncator

from .models import Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """
    Список подразделений в виде «карточек» с кнопкой редактирования
    и ссылкой на связанные мероприятия.
    """
    list_display = ("card",)
    list_display_links = ("card",)
    search_fields = ("name", "description")
    list_per_page = 30

    # Переиспользуем те же стили, что и у EventAdmin
    class Media:
        css = {"all": ("events/admin.css",)}

    def card(self, obj: Department):
        # URL редактирования подразделения
        edit_url = reverse("admin:departments_department_change", args=[obj.pk])
        # URL списка мероприятий, отфильтрованных по подразделению
        events_url = reverse("admin:events_event_changelist") + f"?department__id__exact={obj.pk}"

        # Подсчёты (аккуратно, если связей нет)
        try:
            events_count = obj.event_set.count()
        except Exception:
            events_count = None

        # Кастомный User с FK на Department обычно даёт обратную связь user_set,
        # если не задан related_name на поле department у users.User
        try:
            users_count = obj.user_set.count()
        except Exception:
            # Если у модели User задано related_name='users' — можно раскомментировать:
            # users_count = obj.users.count()
            users_count = None

        # Описание (если поле есть)
        desc = getattr(obj, "description", None)
        if desc:
            short = Truncator(desc).chars(260)
            has_more = short != desc
            details = "" if not has_more else format_html(
                '<details class="evt-details"><summary>показать полностью</summary><div>{}</div></details>',
                desc.replace("\n", "<br/>"),
            )
            desc_html = format_html("{}{}", short if not has_more else short + "…", details)
        else:
            desc_html = "—"

        # Мета (если есть created_at/updated_at — отобразим; иначе «—»)
        created = getattr(obj, "created_at", None) or "—"
        updated = getattr(obj, "updated_at", None) or "—"

        return format_html(
            """
            <div class="evt-card">
              <div class="evt-head">
                <span class="evt-title" style="font-size:15px;font-weight:600;">{name}</span>
              </div>

              <div class="evt-toolbar">
                <a class="evt-btn" href="{edit}">✏️ Изменить</a>
                <a class="evt-btn" href="{events}">🗂 Показать мероприятия этого подразделения{suffix_events}</a>
              </div>

              <div class="evt-grid">
                <div><b>ID:</b> {id}</div>
                <div><b>Всего мероприятий:</b> {events_count}</div>
                <div><b>Всего пользователей:</b> {users_count}</div>
              </div>

              <div class="evt-desc">
                <b>Описание:</b><br/>{desc}
              </div>

              <div class="evt-meta">
                <span>Создано: {created}</span>
                <span>Обновлено: {updated}</span>
              </div>
            </div>
            """,
            name=obj.name,
            edit=edit_url,
            events=events_url,
            suffix_events="" if events_count is None else f" ({events_count})",
            id=obj.pk,
            events_count="—" if events_count is None else events_count,
            users_count="—" if users_count is None else users_count,
            desc=desc_html,
            created=created,
            updated=updated,
        )

    card.short_description = "Подразделение"
