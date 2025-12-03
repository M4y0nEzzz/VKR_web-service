# categories/admin.py
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.text import Truncator

from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Список категорий в виде «карточек» с быстрым переходом к редактированию
    и ссылкой на связанные мероприятия.
    """
    list_display = ("card",)
    list_display_links = ("card",)
    search_fields = ("name",)
    list_per_page = 30

    # можно переиспользовать css из events, чтобы карточки выглядели так же
    class Media:
        css = {"all": ("events/admin.css",)}  # файл уже подключён у EventAdmin

    def card(self, obj: Category):
        # Кнопка "Изменить"
        edit_url = reverse("admin:categories_category_change", args=[obj.pk])
        # Ссылка на список мероприятий, отфильтрованный по этой категории
        events_url = reverse("admin:events_event_changelist") + f"?category__id__exact={obj.pk}"

        # Цвет (если поле есть) — красивый бейдж
        color = getattr(obj, "color", None)
        color_html = ""
        if color:
            color_html = format_html(
                '<span style="display:inline-flex;align-items:center;gap:6px;">'
                '<span style="width:12px;height:12px;border-radius:3px;'
                'background:{};border:1px solid rgba(0,0,0,.25);display:inline-block;"></span>'
                '<code style="opacity:.8;">{}</code>'
                "</span>",
                color,
                color,
            )

        # Сколько мероприятий в этой категории (если связь есть)
        try:
            events_count = obj.event_set.count()
        except Exception:
            events_count = None

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

        # Мета (если есть создано/обновлено — просто отобразим как есть)
        created = getattr(obj, "created_at", None)
        updated = getattr(obj, "updated_at", None)

        return format_html(
            """
            <div class="evt-card">
              <div class="evt-head">
                <span class="evt-title" style="font-size:15px;font-weight:600;">{name}</span>
                <span style="margin-left:auto;">{color}</span>
              </div>

              <div class="evt-toolbar">
                <a class="evt-btn" href="{edit}">✏️ Изменить</a>
                <a class="evt-btn" href="{events}">🗂 Показать мероприятия этой категории{suffix}</a>
              </div>

              <div class="evt-grid">
                <div><b>ID:</b> {id}</div>
                <div><b>Всего мероприятий:</b> {count}</div>
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
            color=color_html or "—",
            edit=edit_url,
            events=events_url,
            suffix="" if events_count is None else f" ({events_count})",
            id=obj.pk,
            count="—" if events_count is None else events_count,
            desc=desc_html,
            created=created or "—",
            updated=updated or "—",
        )

    card.short_description = "Категория"
