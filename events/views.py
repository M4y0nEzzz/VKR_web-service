from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .forms import EventForm
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Side, Font, PatternFill
from collections import defaultdict
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Event
from django.conf import settings
from django.utils import timezone
from datetime import datetime as dt


def event_list(request):
    events = Event.objects.all()
    return render(request, 'events/event_list.html', {'events': events})


def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)

            if form.cleaned_data['responsible']:
                event.responsible = form.cleaned_data['responsible']

            event.save()
            return redirect('events_ui')

        else:
            return render(request, 'events/create_event.html', {'form': form})

    else:
        form = EventForm()

    return render(request, 'events/create_event.html', {'form': form})


def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.delete()
    return redirect('events_ui')


def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            return redirect('events_ui')
    else:
        form = EventForm(instance=event)

    return render(request, 'events/edit_event.html', {
        'form': form,
        'event': event,
        'title': 'Редактирование мероприятия'
    })


def export_events_to_excel(request):
    from io import BytesIO
    import openpyxl

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = "Мероприятия"

    headers = [
        "ID", "Название", "Дата начала", "Дата окончания", "Категория",
        "Подразделение", "Ответственный", "Место", "Создатель", "Комментарий"
    ]
    worksheet.append(headers)

    events = Event.objects.all()
    for event in events:
        worksheet.append([
            event.id,
            event.name or "",
            event.date.strftime('%Y-%m-%d %H:%M') if event.date else "",
            event.end_date.strftime('%Y-%m-%d %H:%M') if event.end_date else "",
            event.category.name if event.category else "",
            event.department.name if event.department else "",
            ", ".join([user.displayname for user in event.responsible.all()]),
            event.place or "",
            event.user.username if event.user else "",
            event.comment or "",
        ])

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response['Content-Disposition'] = 'attachment; filename="events_export.xlsx"'
    return response


def bulk_delete_events(request):
    if request.method == 'POST':
        selected_events = request.POST.getlist('selected_events')
        if selected_events:
            try:
                event_ids = [int(id) for id in selected_events]
                # Удаляем мероприятия
                Event.objects.filter(id__in=event_ids).delete()

                # Сообщение об успехе
                from django.contrib import messages
                count = len(selected_events)
                if count == 1:
                    messages.success(request, 'Мероприятие успешно удалено!')
                else:
                    messages.success(request, f'{count} мероприятий успешно удалено!')
            except (ValueError, Event.DoesNotExist):
                messages.error(request, 'Ошибка при удалении мероприятий')

        return redirect('events_ui')


def events_ui(request):
    current_year = dt.now().year

    month_str = request.GET.get('month', '')
    year_str = request.GET.get('year', '')
    sort_order = request.GET.get('sort_order', 'desc')

    print("=" * 60)
    print(f"ПРОСТАЯ ФИЛЬТРАЦИЯ")
    print(f"Получено: month='{month_str}', year='{year_str}'")

    # Начинаем с всех событий
    events = Event.objects.all()

    # Проверяем, что месяц и год - валидные числа
    month_int = None
    year_int = None

    if month_str and month_str.strip() and month_str != 'None':
        try:
            month_int = int(month_str)
            if not (1 <= month_int <= 12):
                month_int = None
                print(f"  Месяц {month_str} вне диапазона 1-12")
        except (ValueError, TypeError) as e:
            print(f"  Ошибка преобразования месяца '{month_str}': {e}")

    if year_str and year_str.strip() and year_str != 'None':
        try:
            year_int = int(year_str)
        except (ValueError, TypeError) as e:
            print(f"  Ошибка преобразования года '{year_str}': {e}")
            year_int = None

    # Применяем фильтры
    if month_int and year_int:
        # И месяц, и год указаны
        print(f"  Фильтрация: месяц={month_int}, год={year_int}")
        events = events.filter(
            Q(date__month=month_int, date__year=year_int) |
            Q(end_date__month=month_int, end_date__year=year_int)
        )
        print(f"  Найдено: {events.count()} событий")

    elif year_int:
        # Только год указан
        print(f"  Фильтрация только по году: {year_int}")
        events = events.filter(
            Q(date__year=year_int) | Q(end_date__year=year_int)
        )
        print(f"  Найдено: {events.count()} событий")

    elif month_int:
        # Только месяц указан (используем текущий год)
        current_year_for_filter = current_year
        print(f"  Фильтрация только по месяцу: {month_int} (год={current_year_for_filter})")
        events = events.filter(
            Q(date__month=month_int, date__year=current_year_for_filter) |
            Q(end_date__month=month_int, end_date__year=current_year_for_filter)
        )
        print(f"  Найдено: {events.count()} событий")

    # Сортировка
    if sort_order == 'asc':
        events = events.order_by('date')
        print("  Сортировка по возрастанию")
    else:
        events = events.order_by('-date')
        print("  Сортировка по убыванию")

    print(f"  Итоговое количество: {events.count()}")
    print("=" * 60)

    # Пагинация
    paginator = Paginator(events, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Обрабатываем ответственных для отображения
    for event in page_obj:
        if event.responsible:
            event.responsible_list = event.responsible.split(',')
        else:
            event.responsible_list = []

    # Подготавливаем значения для шаблона
    month_for_template = str(month_int) if month_int else ''
    year_for_template = str(year_int) if year_int else ''

    context = {
        'page_obj': page_obj,
        'month': month_for_template,
        'year': year_for_template,
        'sort_order': sort_order,
        'current_year': current_year,
    }

    return render(request, 'events/eventsUI.html', context)


@csrf_exempt
@require_POST
def export_selected_events(request):
    selected_events_ids = request.POST.getlist('selected_events')
    if not selected_events_ids:
        return HttpResponse("Не выбрано ни одного мероприятия", status=400)

    queryset = Event.objects.filter(id__in=selected_events_ids)

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "План мероприятий"

    column_widths = {
        'A': 15,
        'C': 40,
        'D': 35,
        'E': 30,
    }

    for col, width in column_widths.items():
        worksheet.column_dimensions[col].width = width

    header_font = Font(bold=True, size=12)
    center_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    left_alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    current_row = 1

    for _ in range(3):
        current_row += 1

    worksheet.merge_cells(f'D{current_row}:E{current_row}')
    worksheet.cell(row=current_row, column=4, value='УТВЕРЖДАЮ').alignment = center_alignment
    worksheet.cell(row=current_row, column=4).font = Font(bold=True)
    current_row += 1

    worksheet.merge_cells(f'D{current_row}:E{current_row}')
    worksheet.cell(row=current_row, column=4, value='Ректор ВоГУ').alignment = center_alignment
    current_row += 1
    worksheet.merge_cells(f'D{current_row}:E{current_row}')
    worksheet.cell(row=current_row, column=4, value='').alignment = center_alignment
    current_row += 1

    worksheet.cell(row=current_row, column=4, value='').alignment = center_alignment
    worksheet.cell(row=current_row, column=5, value='Д. В. Дворников').alignment = center_alignment
    current_row += 1

    worksheet.cell(row=current_row, column=4, value='').alignment = center_alignment
    worksheet.cell(row=current_row, column=5, value='2025 года').alignment = center_alignment
    current_row += 2

    worksheet.merge_cells(f'A{current_row}:E{current_row}')
    worksheet.cell(row=current_row, column=1, value='ПЛАН МЕРОПРИЯТИЙ УНИВЕРСИТЕТА')
    worksheet.cell(row=current_row, column=1).alignment = center_alignment
    worksheet.cell(row=current_row, column=1).font = Font(bold=True, size=14)
    current_row += 2

    headers = [
        "Дата, время",
        "Наименование мероприятия",
        "Место проведения мероприятия",
        "Структурное подразделение",
        "Ответственный работник"
    ]

    header_row = current_row
    for col_num, header in enumerate(headers, 1):
        cell = worksheet.cell(row=header_row, column=col_num, value=header)
        cell.font = header_font
        cell.alignment = center_alignment
        cell.border = thin_border
        cell.fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")

    current_row += 1

    events_by_category = defaultdict(list)

    for event in queryset.order_by('category__name', 'date'):
        if event.category:
            events_by_category[event.category.name].append(event)
        else:
            events_by_category['Без категории'].append(event)

    for category_name, events in events_by_category.items():
        if category_name and events:
            worksheet.merge_cells(f'A{current_row}:E{current_row}')
            category_cell = worksheet.cell(row=current_row, column=1, value=category_name.upper())
            category_cell.font = Font(bold=True, size=11)
            category_cell.alignment = left_alignment
            current_row += 1

            for event in events:
                date_str = ""
                if event.date:
                    date_str = event.date.strftime('%Y.%m.%d %H:%M')
                    if event.end_date:
                        date_str += f" - {event.end_date.strftime('%H:%M' if event.date.date() == event.end_date.date() else '%Y.%m.%d %H:%M')}"

                responsible_names = event.responsible or ""

                worksheet.cell(row=current_row, column=1, value=date_str).alignment = left_alignment
                worksheet.cell(row=current_row, column=2, value=event.name).alignment = left_alignment
                worksheet.cell(row=current_row, column=3, value=event.place or "").alignment = left_alignment
                worksheet.cell(row=current_row, column=4,
                               value=event.department.name if event.department else "").alignment = left_alignment
                worksheet.cell(row=current_row, column=5, value=responsible_names).alignment = left_alignment

                for col_num in range(1, 6):
                    cell = worksheet.cell(row=current_row, column=col_num)
                    cell.border = thin_border
                    cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

                current_row += 1

    for row in worksheet.iter_rows(min_row=header_row, max_row=current_row - 1, max_col=5):
        for cell in row:
            if cell.value:
                lines = str(cell.value).count('\n') + 1
                char_count = len(str(cell.value))
                estimated_height = min(100, max(15, lines * 15 + (char_count // 100) * 5))
                worksheet.row_dimensions[cell.row].height = estimated_height

    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response['Content-Disposition'] = 'attachment; filename="План мероприятий.xlsx"'
    return response



def check_database(request):
    results = {
        'total_events': Event.objects.count(),
        'events_with_date': Event.objects.filter(date__isnull=False).count(),
        'events_with_end_date': Event.objects.filter(end_date__isnull=False).count(),
        'month_distribution': {},
        'sample_events': []
    }

    for month in range(1, 13):
        count = Event.objects.filter(
            Q(date__month=month) | Q(end_date__month=month)
        ).count()
        results['month_distribution'][month] = count

    sample = Event.objects.filter(date__isnull=False).order_by('date')[:5]
    for event in sample:
        results['sample_events'].append({
            'id': event.id,
            'name': event.name,
            'date': event.date,
            'date_month': event.date.month if event.date else None,
            'end_date': event.end_date,
            'end_date_month': event.end_date.month if event.end_date else None,
        })

    from django.http import JsonResponse
    return JsonResponse(results)