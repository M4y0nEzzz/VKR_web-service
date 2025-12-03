# locations/admin.py
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.text import Truncator
from urllib.parse import quote_plus

from .models import Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """
    Список мест проведения в виде «карточек» с быстрым переходом к редактированию
    и ссылкой на связанные мероприятия.
    """
    list_display = ("card",)
    list_display_links = ("card",)
    search_fields = ("name", "address", "description")
    list_per_page = 30

    # Переиспользуем css карточек из событий
    class Media:
        css = {"all": ("events/admin.css",)}

    def card(self, obj: Location):
        # URL редактирования места
        edit_url = reverse("admin:locations_location_change", args=[obj.pk])
        # URL списка мероприятий, отфильтрованных по этому месту (ManyToMany фильтр)
        events_url = reverse("admin:events_event_changelist") + f"?locations__id__exact={obj.pk}"

        # Счётчик связанных мероприятий (через обратную M2M-связь)
        try:
            events_count = obj.event_set.count()
        except Exception:
            events_count = None

        # Адрес и ссылка «Открыть на карте»
        address = getattr(obj, "address", None)
        map_link = ""
        if address:
            map_url = f"https://maps.google.com/?q={quote_plus(address)}"
            map_link = format_html('<a class="evt-btn" href="{}" target="_blank" rel="noopener">🗺 Открыть на карте</a>', map_url)

        # Описание (с возможностью развернуть)
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

        # Метаданные, если есть поля аудита
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
                <a class="evt-btn" href="{events}">🗂 Показать мероприятия в этом месте{suffix_events}</a>
                {map_link}
              </div>

              <div class="evt-grid">
                <div><b>ID:</b> {id}</div>
                <div><b>Всего мероприятий:</b> {events_count}</div>
                <div style="grid-column: 1 / -1;"><b>Адрес:</b> {address}</div>
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
            address=address or "—",
            desc=desc_html,
            created=created,
            updated=updated,
            map_link=map_link or "",
        )

    card.short_description = "Место проведения"
