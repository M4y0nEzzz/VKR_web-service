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
        'status',
        'date_start',
        'date_end',
        'category',
        'department',
        'responsible',
        'created_at',
        'updated_at',
        'is_published',
        'created_by_display'
    )

    list_filter = (
        'status',
        'category',
        'department',
        'date_start',
        'is_published'
    )

    search_fields = (
        'title',
        'description'
    )

    filter_horizontal = (
        'participants',
    )

    list_editable = (
        'status',
    )



    # Быстрые действия

    actions = [
        "mark_as_completed",
        "mark_as_cancelled",
        "mark_as_planned",
        "export_to_excel",
    ]


    # Изменение статуса мероприятия
    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
        self.message_user(request, 'Выбранные мероприятия отмечены как завершенные ✅')
    mark_as_completed.short_description = 'Отметить как завершенные'

    def mark_as_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
        self.message_user(request, 'Выбранные мероприятия отмечены как отмененные ❌')
    mark_as_cancelled.short_description = 'Отметить как отмененные'

    def mark_as_planned(self, request, queryset):
        queryset.update(status='planned')
        self.message_user(request, 'Выбранные мероприятия снова запланированы 🔄')

    mark_as_planned.short_description = 'Отметить как запланированные'

    autocomplete_fields = (
        'responsible',
        'participants',
        'category',
        'department'
    )

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



    # Экспорт отчетов (пока только Excel)

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
            'Участники'
        ]
        worksheet.append(headers)

        for event in queryset:
            participants = ", ".join([str(u) for u in event.participants.all()])
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
            ])

        # Сохранение в поток
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


    # Отображение создателя записи (мероприятия)
    def created_by_display(self, obj):
        return obj.created_by.username if obj.created_by else "Не указан"
    created_by_display.short_description = "Создатель записи"


    # Отображение мест проведения
    def locations_display(self, obj):
        return ", ".join([location.name for location in obj.locations.all()])
    locations_display.short_description = "Места проведения"

