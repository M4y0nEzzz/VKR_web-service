from django.contrib import admin, messages
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils import timezone
from django.utils.formats import date_format
from .models import Event
import openpyxl
from io import BytesIO
from django.contrib import admin
from django import forms


def _fmt_dt(dt):
    if not dt:
        return "—"
    dt = timezone.localtime(dt) if timezone.is_aware(dt) else dt
    return date_format(dt, "j E Y г. H:i")


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = "__all__"
        widgets = {
            'description': forms.Textarea(attrs={'class': 'mc-textarea', 'rows': 4, 'placeholder': 'Описание события'}),
            'title': forms.TextInput(attrs={'class': 'mc-input', 'placeholder': 'Заголовок мероприятия'}),
            'date_start': forms.DateTimeInput(attrs={'class': 'mc-input', 'type': 'datetime-local'}),
            'date_end': forms.DateTimeInput(attrs={'class': 'mc-input', 'type': 'datetime-local'}),
        }


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
        css = {"all": ("events/admin-card.css",)}

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
        messages.success(request, f'{"Опубликовано" if obj.is_published else "Снято с публикации"}')
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

    def card(self, obj: Event):
        status_to_cls = {
            "planned": "mc-chip--planned",
            "ongoing": "mc-chip--ongoing",
            "completed": "mc-chip--completed",
            "cancelled": "mc-chip--cancelled",
        }
        status_label = dict(Event.STATUS_CHOICES).get(obj.status, obj.status or "—")
        status_chip = format_html('<span class="mc-chip {}">{}</span>', status_to_cls.get(obj.status, ""), status_label)
        pub_chip = format_html('<span class="mc-chip {}">{}</span>',
                               "mc-chip--ok" if obj.is_published else "mc-chip--bad",
                               "Опубликовано" if obj.is_published else "Не опубликовано")

        locations = ", ".join(obj.locations.values_list("name", flat=True)) or "—"
        participants = ", ".join(map(str, obj.participants.all())) or "—"
        desc = (obj.description or "—").replace("\n", "<br/>")

        return format_html(
            '''
            <div class="mc-card">
              <div class="mc-head">
                <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
                  <span class="mc-id">#{id}</span>
                  <h2 class="mc-title">{title}</h2>
                </div>
              </div>

              <div class="mc-chips">{status_chip} {pub_chip}</div>

              <div class="mc-grid">
                <div class="mc-box"><div class="mc-label">Даты</div><p class="mc-val">{date_start} — {date_end}</p></div>
                <div class="mc-box"><div class="mc-label">Категория</div><p class="mc-val">{category}</p></div>
                <div class="mc-box"><div class="mc-label">Подразделение</div><p class="mc-val">{department}</p></div>
                <div class="mc-box"><div class="mc-label">Ответственный</div><p class="mc-val">{responsible}</p></div>
                <div class="mc-box"><div class="mc-label">Участники</div><p class="mc-val">{participants}</p></div>
                <div class="mc-box"><div class="mc-label">Места</div><p class="mc-val">{locations}</p></div>
                <div class="mc-box"><div class="mc-label">Создатель</div><p class="mc-val">{creator}</p></div>
                <div class="mc-box"><div class="mc-label">Публикация</div><p class="mc-val">{pub_text}</p></div>
              </div>

              <div class="mc-box" style="margin-top:12px">
                <div class="mc-label">Описание</div>
                <div class="mc-prose">{desc}</div>
              </div>

              <div class="mc-meta">
                <div>Создано: {created}</div><div>Обновлено: {updated}</div>
              </div>
            </div>
            ''',
            id=obj.pk, title=obj.title,
            status_chip=status_chip, pub_chip=pub_chip,
            date_start=date_format(obj.date_start, "j E Y, H:i"),
            date_end=(date_format(obj.date_end, "j E Y, H:i") if obj.date_end else "—"),
            category=getattr(obj.category, "name", "—"),
            department=getattr(obj.department, "name", "—"),
            responsible=getattr(getattr(obj, "responsible", None), "username", "—"),
            participants=participants, locations=locations,
            creator=getattr(getattr(obj, "created_by", None), "username", "—"),
            pub_text=("Опубликовано" if obj.is_published else "Не опубликовано"),
            desc=desc,
            created=(date_format(getattr(obj, "created_at", None), "j E Y в H:i") if getattr(obj, "created_at",
                                                                                             None) else "—"),
            updated=(date_format(getattr(obj, "updated_at", None), "j E Y в H:i") if getattr(obj, "updated_at",
                                                                                             None) else "—"),
        )

    card.short_description = "Мероприятие"

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
