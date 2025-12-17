from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.utils.formats import date_format
from django import forms
from .models import Event
from io import BytesIO
import openpyxl
from django.http import HttpResponse
from openpyxl.styles import Alignment

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

    search_fields = (
        "name",
        "comment",
        "responsible",
        "place",
        "category__name",
        "department__name",
        "user__username",
    )

    list_filter = (
        "category",
        "department",
        "date",
    )

    class Media:
        css = {"all": ("events/admin-card.css",)}

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("category", "department", "user").distinct()

    def card(self, obj: Event):
        return format_html(
            """
            <div class="mc-card">
              <div class="mc-head">
                <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
                  <span class="mc-id">#{id}</span>
                  <h2 class="mc-title">{title}</h2>
                </div>
              </div>

              <div class="mc-grid">
                <div class="mc-box"><div class="mc-label">Даты</div><p class="mc-val">{date} — {end_date}</p></div>
                <div class="mc-box"><div class="mc-label">Категория</div><p class="mc-val">{category}</p></div>
                <div class="mc-box"><div class="mc-label">Подразделение</div><p class="mc-val">{department}</p></div>
                <div class="mc-box"><div class="mc-label">Ответственный</div><p class="mc-val">{responsible}</p></div>
                <div class="mc-box"><div class="mc-label">Место</div><p class="mc-val">{place}</p></div>
                <div class="mc-box"><div class="mc-label">Создатель</div><p class="mc-val">{creator}</p></div>
              </div>

              <div class="mc-box" style="margin-top:12px">
                <div class="mc-label">Комментарий</div>
                <div class="mc-prose">{comment}</div>
              </div>
            </div>
            """,
            id=obj.pk,
            title=obj.name or "—",
            date=_fmt_dt(obj.date),
            end_date=_fmt_dt(obj.end_date),
            category=getattr(obj.category, "name", "—"),
            department=getattr(obj.department, "name", "—"),
            responsible=obj.responsible or "—",
            place=obj.place or "—",
            creator = obj.user.displayname if obj.user else "—",
            comment=(obj.comment or "—").replace("\n", "<br/>"),
        )

    card.short_description = "Мероприятие"

    # Экспорт в Excel
    def export_to_excel(self, request, queryset):
        # Создание нового Excel файла
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = "План мероприятий"

        # Заголовки для таблицы
        headers = [
            "№", "Название мероприятия", "Дата начала", "Дата окончания", "Категория",
            "Подразделение", "Ответственные", "Место проведения", "Комментарий"
        ]

        # Добавление заголовков в первую строку
        for col_num, header in enumerate(headers, 1):
            worksheet.cell(row=1, column=col_num, value=header)

        # Настройка выравнивания для заголовков
        for col_num in range(1, len(headers) + 1):
            worksheet.cell(row=1, column=col_num).alignment = Alignment(horizontal='center', vertical='center')

        # Заполнение строк данными
        row_num = 2  # Начнем с второй строки
        for idx, event in enumerate(queryset, start=1):
            responsible_names = event.responsible  # Просто берем строку
            worksheet.cell(row=row_num, column=1, value=idx)  # Номер мероприятия
            worksheet.cell(row=row_num, column=2, value=event.name)  # Название мероприятия
            worksheet.cell(row=row_num, column=3,
                           value=event.date.strftime('%d-%m-%Y %H:%M') if event.date else "")  # Дата начала
            worksheet.cell(row=row_num, column=4,
                           value=event.end_date.strftime('%d-%m-%Y %H:%M') if event.end_date else "")  # Дата окончания
            worksheet.cell(row=row_num, column=5, value=event.category.name if event.category else "")  # Категория
            worksheet.cell(row=row_num, column=6,
                           value=event.department.name if event.department else "")  # Подразделение
            worksheet.cell(row=row_num, column=7, value=responsible_names or "")  # Ответственные (строка)
            worksheet.cell(row=row_num, column=8, value=event.place)  # Место проведения
            worksheet.cell(row=row_num, column=9, value=event.comment)  # Комментарий

            row_num += 1

        # Выравнивание текста в ячейках
        for row in worksheet.iter_rows(min_row=2, min_col=1, max_col=9, max_row=row_num - 1):
            for cell in row:
                cell.alignment = Alignment(horizontal='left', vertical='center')

        # Сохранение файла в буфер
        output = BytesIO()
        workbook.save(output)
        output.seek(0)

        # Отправка файла в ответ
        response = HttpResponse(
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response['Content-Disposition'] = 'attachment; filename="plan_meropriyatiy.xlsx"'
        return response

    export_to_excel.short_description = "Экспортировать в Excel"

    # Register the action for exporting to Excel
    actions = [export_to_excel]