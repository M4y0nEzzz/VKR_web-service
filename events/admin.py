from django.contrib import admin
from django.utils.html import format_html
from .models import Event
import openpyxl
from django.http import HttpResponse
from io import BytesIO


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'title',
        'colored_status',
        'date_start',
        'date_end',
        'category',
        'department',
        'responsible',
        'locations_display',
        'is_published',
        'created_by_display',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'status',
        'category',
        'department',
        'date_start',
        'is_published',
        'locations',
    )

    search_fields = (
        'title',
        'description',
        'category__name',
        'department__name',
        'responsible__username',
    )

    filter_horizontal = (
        'participants',
        'locations',
    )

    list_editable = (
        # 'status',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'created_by',
    )

    actions = [
        "mark_as_completed",
        "mark_as_cancelled",
        "mark_as_planned",
        "mark_as_published",
        "mark_as_unpublished",
        "export_to_excel",
    ]



    # ---------- БЫСТРЫЕ ДЕЙСТВИЯ СО СТАТУСОМ ----------

    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
        self.message_user(request, 'Выбранные мероприятия отмечены как завершенные')
    mark_as_completed.short_description = 'Отметить как завершенные'

    def mark_as_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
        self.message_user(request, 'Выбранные мероприятия отмечены как отмененные')
    mark_as_cancelled.short_description = 'Отметить как отмененные'

    def mark_as_planned(self, request, queryset):
        queryset.update(status='planned')
        self.message_user(request, 'Выбранные мероприятия снова запланированы')
    mark_as_planned.short_description = 'Отметить как запланированные'



    # ---------- БЫСТРЫЕ ДЕЙСТВИЯ ПО ПУБЛИКАЦИИ ----------
    def mark_as_published(self, request, queryset):
        queryset.update(is_published=True)
        self.message_user(request, 'Выбранные мероприятия отмечены как опубликованные')
    mark_as_published.short_description = 'Опубликовать выбранные'

    def mark_as_unpublished(self, request, queryset):
        queryset.update(is_published=False)
        self.message_user(request, 'Выбранные мероприятия сняты с публикации')
    mark_as_unpublished.short_description = 'Снять с публикации'



    # ---------- АВТОПОДСТАНОВКА СОЗДАТЕЛЯ ----------
    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)



    # ---------- ОТОБРАЖЕНИЕ ПОЛЕЙ ДЛЯ СПИСКА ----------

    def created_by_display(self, obj):
        return obj.created_by.username if obj.created_by else "—"
    created_by_display.short_description = "Создатель"

    def locations_display(self, obj):
        locations = obj.locations.all()
        if not locations:
            return "—"
        return ", ".join([loc.name for loc in locations])
    locations_display.short_description = "Места проведения"



    # ---------- ЦВЕТНОЙ СТАТУС В СПИСКЕ ----------

    def colored_status(self, obj):
        colors = {
            'planned': 'blue',      # Запланировано
            'ongoing': 'green',     # В процессе
            'completed': 'gray',    # Завершено
            'cancelled': 'red',     # Отменено
        }
        color = colors.get(obj.status, "black")
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    colored_status.short_description = 'Статус'



    # ---------- ЭКСПОРТ В EXCEL ----------

    def export_to_excel(self, request, queryset):
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = 'Мероприятия'

        headers = [
            'ID',
            'Название',
            'Статус',
            'Дата начала',
            'Дата окончания',
            'Категория',
            'Подразделение',
            'Ответственный',
            'Участники',
            'Места проведения',
            'Опубликовано',
            'Создатель',
        ]
        worksheet.append(headers)

        for event in queryset:
            participants = ", ".join([str(u) for u in event.participants.all()])
            locations = ", ".join([str(l) for l in event.locations.all()])
            worksheet.append([
                event.id,
                event.title,
                event.get_status_display(),
                event.date_start.strftime('%Y-%m-%d %H:%M') if event.date_start else '',
                event.date_end.strftime('%Y-%m-%d %H:%M') if event.date_end else '',
                event.category.name if event.category else '',
                event.department.name if event.department else '',
                event.responsible.username if event.responsible else '',
                participants,
                locations,
                'Да' if event.is_published else 'Нет',
                event.created_by.username if event.created_by else '',
            ])

        output = BytesIO()
        workbook.save(output)
        output.seek(0)

        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="events_export.xlsx"'
        return response

    export_to_excel.short_description = 'Экспортировать в Excel'
