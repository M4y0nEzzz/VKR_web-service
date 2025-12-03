# events/admin.py
from django.contrib import admin, messages
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.text import Truncator
from django.utils import timezone
from django.utils.formats import date_format

from .models import Event

import openpyxl
from io import BytesIO


def _fmt_dt(dt):
    if not dt:
        return "—"
    dt = timezone.localtime(dt) if timezone.is_aware(dt) else dt
    return date_format(dt, "j E Y г. H:i")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("card",)
    list_display_links = ("card",)
    list_per_page = 20

    list_filter = ("status", "category", "department", "date_start", "is_published", "locations")
    search_fields = ("title", "description", "category__name", "department__name", "responsible__username")

    filter_horizontal = ("participants", "locations")
    readonly_fields = ("created_at", "updated_at", "created_by")

    actions = [
        "mark_as_completed",
        "mark_as_cancelled",
        "mark_as_planned",
        "mark_as_published",
        "mark_as_unpublished",
        "export_to_excel",
    ]

    class Media:
        css = {"all": ("events/admin.css",)}

    # --- custom admin URLs (names live under the 'admin' namespace) ---
    def get_urls(self):
        urls = super().get_urls()
        my = [
            path(
                "<int:pk>/toggle-publish/",
                self.admin_site.admin_view(self.toggle_publish),
                name="events_event_toggle_publish",
            ),
            path(
                "<int:pk>/set-status/<str:status>/",
                self.admin_site.admin_view(self.set_status),
                name="events_event_set_status",
            ),
        ]
        return my + urls

    def _back(self, request, fallback=".."):
        return HttpResponseRedirect(request.META.get("HTTP_REFERER") or fallback)

    # --- handlers for quick actions ---
    def toggle_publish(self, request, pk):
        obj = Event.objects.filter(pk=pk).first()
        if not obj:
            messages.error(request, "Мероприятие не найдено.")
            return self._back(request)

        if not self.has_change_permission(request, obj):
            messages.error(request, "Недостаточно прав для изменения публикации.")
            return self._back(request)

        obj.is_published = not obj.is_published
        obj.save(update_fields=["is_published", "updated_at"])
        messages.success(request, f'Публикация: {"включена" if obj.is_published else "выключена"}')
        return self._back(request, fallback=reverse("admin:events_event_changelist"))

    def set_status(self, request, pk, status):
        allowed = {"planned", "ongoing", "completed", "cancelled"}
        if status not in allowed:
            messages.error(request, "Некорректный статус.")
            return self._back(request)

        obj = Event.objects.filter(pk=pk).first()
        if not obj:
            messages.error(request, "Мероприятие не найдено.")
            return self._back(request)

        if not self.has_change_permission(request, obj):
            messages.error(request, "Недостаточно прав для изменения статуса.")
            return self._back(request)

        obj.status = status
        obj.save(update_fields=["status", "updated_at"])
        messages.success(request, f"Статус изменён на «{obj.get_status_display()}».")
        return self._back(request, fallback=reverse("admin:events_event_changelist"))

    # --- card renderer ---
    def card(self, obj: Event):
        colors = {
            "planned": "#3b82f6",
            "ongoing": "#22c55e",
            "completed": "#9ca3af",
            "cancelled": "#ef4444",
        }
        color = colors.get(obj.status, "#d1d5db")

        # IMPORTANT: URLs must be under the 'admin' namespace
        edit_url = reverse("admin:events_event_change", args=[obj.pk])
        toggle_url = reverse("admin:events_event_toggle_publish", args=[obj.pk])
        set_status = lambda s: reverse("admin:events_event_set_status", args=[obj.pk, s])

        locations = ", ".join(obj.locations.values_list("name", flat=True)) or "—"
        participants = ", ".join(map(str, obj.participants.all())) or "—"

        raw_desc = obj.description or "—"
        short = Truncator(raw_desc).chars(260)
        has_more = short != raw_desc

        pub_badge = format_html(
            '<span style="display:inline-flex;align-items:center;gap:6px;">'
            '<span style="width:10px;height:10px;border-radius:50%;background:{};display:inline-block;"></span>'
            '{}'
            "</span>",
            "#22c55e" if obj.is_published else "#ef4444",
            "Опубликовано" if obj.is_published else "Не опубликовано",
        )

        toolbar = format_html(
            """
            <div class="evt-toolbar">
              <a class="evt-btn" href="{edit}">✏️ Изменить</a>
              <a class="evt-btn" href="{toggle}">{pub_action}</a>
              <span class="evt-split"></span>
              <span class="evt-label">Статус:</span>
              <a class="evt-link" href="{s_pl}">Запланировано</a>
              <a class="evt-link" href="{s_on}">В процессе</a>
              <a class="evt-link" href="{s_cm}">Завершено</a>
              <a class="evt-link" href="{s_cc}">Отменено</a>
            </div>
            """,
            edit=edit_url,
            toggle=toggle_url,
            pub_action="Снять с публикации" if obj.is_published else "Опубликовать",
            s_pl=set_status("planned"),
            s_on=set_status("ongoing"),
            s_cm=set_status("completed"),
            s_cc=set_status("cancelled"),
        )

        return format_html(
            """
            <div class="evt-card">
              <div class="evt-head">
                <span class="evt-id">#{id}</span>
                <span class="evt-title">{title}</span>
                <span class="evt-status" style="color:{color};">{status}</span>
              </div>

              {toolbar}

              <div class="evt-grid">
                <div><b>Даты:</b> {start} — {end}</div>
                <div><b>Категория:</b> {category}</div>
                <div><b>Подразделение:</b> {dep}</div>
                <div><b>Ответственный:</b> {resp}</div>
                <div><b>Места:</b> {locs}</div>
                <div><b>Участники:</b> {parts}</div>
                <div><b>Создатель:</b> {creator}</div>
                <div><b>Публикация:</b> {pub}</div>
              </div>

              <div class="evt-desc">
                <b>Описание:</b><br/>
                {short_desc}
                {details}
              </div>

              <div class="evt-meta">
                <span>Создано: {created}</span>
                <span>Обновлено: {updated}</span>
              </div>
            </div>
            """,
            id=obj.id,
            title=obj.title,
            color=color,
            status=obj.get_status_display(),
            toolbar=toolbar,
            start=_fmt_dt(obj.date_start),
            end=_fmt_dt(obj.date_end),
            category=getattr(obj.category, "name", "—"),
            dep=getattr(obj.department, "name", "—"),
            resp=getattr(obj.responsible, "username", "—"),
            locs=locations,
            parts=participants,
            creator=getattr(obj.created_by, "username", "—"),
            pub=pub_badge,
            short_desc=short if not has_more else short + "…",
            details="" if not has_more else format_html(
                '<details class="evt-details"><summary>показать полностью</summary><div>{}</div></details>',
                raw_desc.replace("\n", "<br/>"),
            ),
            created=_fmt_dt(obj.created_at),
            updated=_fmt_dt(obj.updated_at),
        )
    card.short_description = "Мероприятие"

    # --- bulk actions ---
    def mark_as_completed(self, request, queryset):
        queryset.update(status="completed")
        self.message_user(request, "Выбранные мероприятия отмечены как завершенные")
    mark_as_completed.short_description = "Отметить как завершенные"

    def mark_as_cancelled(self, request, queryset):
        queryset.update(status="cancelled")
        self.message_user(request, "Выбранные мероприятия отмечены как отмененные")
    mark_as_cancelled.short_description = "Отметить как отмененные"

    def mark_as_planned(self, request, queryset):
        queryset.update(status="planned")
        self.message_user(request, "Выбранные мероприятия снова запланированы")
    mark_as_planned.short_description = "Отметить как запланированные"

    def mark_as_published(self, request, queryset):
        queryset.update(is_published=True)
        self.message_user(request, "Выбранные мероприятия отмечены как опубликованные")
    mark_as_published.short_description = "Опубликовать выбранные"

    def mark_as_unpublished(self, request, queryset):
        queryset.update(is_published=False)
        self.message_user(request, "Выбранные мероприятия сняты с публикации")
    mark_as_unpublished.short_description = "Снять с публикации"

    # --- created_by autofill ---
    def save_model(self, request, obj, form, change):
        if not change and not getattr(obj, "created_by", None):
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    # --- Excel export ---
    def export_to_excel(self, request, queryset):
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = "Мероприятия"

        headers = [
            "ID",
            "Название",
            "Статус",
            "Дата начала",
            "Дата окончания",
            "Категория",
            "Подразделение",
            "Ответственный",
            "Участники",
            "Места проведения",
            "Опубликовано",
            "Создатель",
        ]
        worksheet.append(headers)

        for event in queryset:
            participants = ", ".join([str(u) for u in event.participants.all()])
            locations = ", ".join([str(l) for l in event.locations.all()])
            worksheet.append([
                event.id,
                event.title,
                event.get_status_display(),
                _fmt_dt(event.date_start),
                _fmt_dt(event.date_end),
                event.category.name if event.category else "",
                event.department.name if event.department else "",
                event.responsible.username if event.responsible else "",
                participants,
                locations,
                "Да" if event.is_published else "Нет",
                event.created_by.username if event.created_by else "",
            ])

        output = BytesIO()
        workbook.save(output)
        output.seek(0)

        response = HttpResponse(
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="events_export.xlsx"'
        return response

    export_to_excel.short_description = "Экспортировать в Excel"
