from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .forms import EventForm
from django.shortcuts import redirect
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Side, Font, PatternFill
from collections import defaultdict
from django.shortcuts import render
from django.core.paginator import Paginator
from .models import Event
from datetime import datetime as dt
from datetime import datetime
from django.http import JsonResponse
from django.db.models import Q
import json
from django.utils import timezone


def save_event_dates(event, dates_data):
    """
    Сохраняет даты мероприятия в комментарий в правильном формате.
    """
    if not dates_data:
        return

    dates_lines = []
    for date_info in dates_data:
        start = date_info.get('start', '')
        end = date_info.get('end', '')
        if start and end:
            dates_lines.append(f"{start} - {end}")

    if dates_lines:
        dates_text = "ДАТЫ:\n" + "\n".join(dates_lines)

        # Сохраняем оригинальный комментарий
        original_comment = event.comment or ''

        # Удаляем старый раздел с датами если есть
        if 'ДАТЫ:' in original_comment:
            lines = original_comment.split('\n')
            clean_lines = []
            in_dates_section = False

            for line in lines:
                line = line.strip()
                if line == 'ДАТЫ:':
                    in_dates_section = True
                    continue
                if in_dates_section and line and '-' in line and 'T' in line:
                    continue
                if line:  # Пропускаем пустые строки
                    clean_lines.append(line)

            original_comment = '\n'.join(clean_lines)

        # Добавляем новые даты
        if original_comment:
            event.comment = f"{original_comment}\n\n{dates_text}"
        else:
            event.comment = dates_text








def event_list(request):
    events = Event.objects.all()
    return render(request, 'events/event_list.html', {'events': events})


def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)

            # Просто устанавливаем user_id из request.user
            if request.user and hasattr(request.user, 'id'):
                event.user_id = request.user.id
            else:
                event.user = None


            # Получаем JSON с датами
            dates_json = request.POST.get('dates_json', '[]')
            try:
                dates_data = json.loads(dates_json)
            except:
                dates_data = []

            # Устанавливаем первую дату как основную (для совместимости)
            if dates_data:
                first_date = dates_data[0]
                try:
                    event.date = timezone.make_aware(
                        datetime.strptime(first_date['start'], '%Y-%m-%dT%H:%M')
                    )
                    event.end_date = timezone.make_aware(
                        datetime.strptime(first_date['end'], '%Y-%m-%dT%H:%M')
                    )
                except:
                    pass

            # Сохраняем все даты в комментарии в правильном формате
            if dates_data:
                # Форматируем даты для сохранения
                dates_lines = []
                for date_info in dates_data:
                    start = date_info.get('start', '')
                    end = date_info.get('end', '')
                    if start and end:
                        # Сохраняем в формате ISO
                        dates_lines.append(f"{start} - {end}")

                if dates_lines:
                    dates_text = "ДАТЫ:\n" + "\n".join(dates_lines)

                    # Получаем оригинальный комментарий из формы
                    original_comment = form.cleaned_data.get('comment', '')

                    # Если в комментарии уже есть даты, заменяем их
                    if original_comment and 'ДАТЫ:' in original_comment:
                        # Удаляем старый раздел с датами
                        lines = original_comment.split('\n')
                        clean_lines = []
                        in_dates_section = False

                        for line in lines:
                            line = line.strip()
                            if line == 'ДАТЫ:':
                                in_dates_section = True
                                continue
                            if in_dates_section and line and '-' in line and 'T' in line:
                                continue
                            if line:  # Пропускаем пустые строки
                                clean_lines.append(line)

                        original_comment = '\n'.join(clean_lines)

                    # Добавляем новые даты к комментарию
                    if original_comment:
                        event.comment = f"{original_comment}\n\n{dates_text}"
                    else:
                        event.comment = dates_text

            event.save()
            return redirect('events_ui')
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
            event = form.save(commit=False)

            # Получаем JSON с датами
            dates_json = request.POST.get('dates_json', '[]')
            try:
                dates_data = json.loads(dates_json)
            except:
                dates_data = []

            # Устанавливаем первую дату как основную (для совместимости)
            if dates_data:
                first_date = dates_data[0]
                try:
                    event.date = timezone.make_aware(
                        datetime.strptime(first_date['start'], '%Y-%m-%dT%H:%M')
                    )
                    event.end_date = timezone.make_aware(
                        datetime.strptime(first_date['end'], '%Y-%m-%dT%H:%M')
                    )
                except:
                    pass

            # Сохраняем все даты в комментарии в правильном формате
            if dates_data:
                # Форматируем даты для сохранения
                dates_lines = []
                for date_info in dates_data:
                    start = date_info.get('start', '')
                    end = date_info.get('end', '')
                    if start and end:
                        # Сохраняем в формате ISO
                        dates_lines.append(f"{start} - {end}")

                if dates_lines:
                    dates_text = "ДАТЫ:\n" + "\n".join(dates_lines)

                    # Получаем оригинальный комментарий из формы
                    original_comment = form.cleaned_data.get('comment', '')

                    # Если в комментарии уже есть даты, заменяем их
                    if original_comment and 'ДАТЫ:' in original_comment:
                        # Удаляем старый раздел с датами
                        lines = original_comment.split('\n')
                        clean_lines = []
                        in_dates_section = False

                        for line in lines:
                            line = line.strip()
                            if line == 'ДАТЫ:':
                                in_dates_section = True
                                continue
                            if in_dates_section and line and '-' in line and 'T' in line:
                                continue
                            if line:  # Пропускаем пустые строки
                                clean_lines.append(line)

                        original_comment = '\n'.join(clean_lines)

                    # Добавляем новые даты к комментарию
                    if original_comment:
                        event.comment = f"{original_comment}\n\n{dates_text}"
                    else:
                        event.comment = dates_text
            else:
                # Если дат нет, удаляем раздел с датами из комментария
                original_comment = form.cleaned_data.get('comment', '')
                if original_comment and 'ДАТЫ:' in original_comment:
                    lines = original_comment.split('\n')
                    clean_lines = []
                    in_dates_section = False

                    for line in lines:
                        line = line.strip()
                        if line == 'ДАТЫ:':
                            in_dates_section = True
                            continue
                        if in_dates_section and line and '-' in line and 'T' in line:
                            continue
                        if line:  # Пропускаем пустые строки
                            clean_lines.append(line)

                    event.comment = '\n'.join(clean_lines).strip()

            event.save()
            return redirect('events_ui')
    else:
        form = EventForm(instance=event)

    return render(request, 'events/edit_event.html', {'form': form, 'event': event})


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

    # Получаем параметры фильтрации (убираем date_range)
    month_str = request.GET.get('month', '')
    year_str = request.GET.get('year', '')
    sort_order = request.GET.get('sort_order', 'desc')
    category_id = request.GET.get('category', '')
    department_id = request.GET.get('department', '')
    search_query = request.GET.get('search', '')
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')

    print("=" * 60)
    print(f"ФИЛЬТРАЦИЯ")
    print(f"Параметры: month='{month_str}', year='{year_str}', category='{category_id}', "
          f"department='{department_id}', search='{search_query}', "
          f"start_date='{start_date_str}', end_date='{end_date_str}'")

    # Базовый queryset
    events = Event.objects.all().select_related('category', 'department')



    # 1. Фильтрация по категории
    if category_id and category_id != '':
        try:
            category_int = int(category_id)
            events = events.filter(category_id=category_int)
            print(f"  Фильтрация по категории ID: {category_int}")
        except ValueError:
            pass

    # 2. Фильтрация по подразделению
    if department_id and department_id != '':
        try:
            department_int = int(department_id)
            events = events.filter(department_id=department_int)
            print(f"  Фильтрация по подразделению ID: {department_int}")
        except ValueError:
            pass

    # 3. Фильтрация по диапазону дат (ОСНОВНОЙ ФИЛЬТР)
    if start_date_str or end_date_str:
        print(f"  Фильтрация по диапазону дат: от '{start_date_str}' до '{end_date_str}'")

        if start_date_str:
            try:
                # Преобразуем строку в datetime
                start_date = dt.strptime(start_date_str, '%Y-%m-%d')
                start_datetime = timezone.make_aware(start_date)
                print(f"    Начальная дата: {start_datetime}")

                # События, которые НАЧИНАЮТСЯ или ЗАКАНЧИВАЮТСЯ после начальной даты
                # ИЛИ происходят в промежутке, включающем начальную дату
                events = events.filter(
                    Q(date__gte=start_datetime) |
                    Q(end_date__gte=start_datetime) |
                    Q(date__lte=start_datetime, end_date__gte=start_datetime)
                )
            except ValueError as e:
                print(f"    Ошибка преобразования start_date: {e}")

        if end_date_str:
            try:
                # Преобразуем строку в datetime (конец дня)
                end_date = dt.strptime(end_date_str, '%Y-%m-%d')
                end_date = end_date.replace(hour=23, minute=59, second=59)
                end_datetime = timezone.make_aware(end_date)
                print(f"    Конечная дата: {end_datetime}")

                # События, которые НАЧИНАЮТСЯ или ЗАКАНЧИВАЮТСЯ до конечной даты
                # ИЛИ происходят в промежутке, включающем конечную дату
                events = events.filter(
                    Q(date__lte=end_datetime) |
                    Q(end_date__lte=end_datetime) |
                    Q(date__lte=end_datetime, end_date__gte=end_datetime)
                )
            except ValueError as e:
                print(f"    Ошибка преобразования end_date: {e}")

    # 4. ПОИСК ПО ТЕКСТУ
    if search_query:
        search_terms = search_query.split()
        search_q = Q()

        for term in search_terms:
            search_q |= (
                    Q(name__icontains=term) |
                    Q(place__icontains=term) |
                    Q(comment__icontains=term) |
                    Q(responsible__icontains=term) |
                    Q(category__name__icontains=term) |
                    Q(department__name__icontains=term)
            )

        events = events.filter(search_q)
        print(f"  Поиск по запросу: '{search_query}'")

    # СОРТИРОВКА
    if sort_order == 'asc':
        events = events.order_by('date', 'name')
        print("  Сортировка по возрастанию")
    else:
        events = events.order_by('-date', 'name')
        print("  Сортировка по убыванию")

    print(f"  Итоговое количество: {events.count()}")
    print("=" * 60)

    # УПРОЩЕННАЯ СТАТИСТИКА (без периодов)
    total_events = Event.objects.count()

    # Пагинация
    paginator = Paginator(events, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Подготавливаем данные для шаблона
    for event in page_obj:
        if event.responsible:
            event.responsible_list = [r.strip() for r in event.responsible.split(',') if r.strip()]
        else:
            event.responsible_list = []

    # Получаем списки для фильтров
    from categories.models import Category
    from departments.models import Department

    categories = Category.objects.all().order_by('name')
    departments = Department.objects.all().order_by('name')

    context = {
        'page_obj': page_obj,
        'sort_order': sort_order,
        'current_year': current_year,
        'search_query': search_query,
        'selected_category': category_id,
        'selected_department': department_id,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'categories': categories,
        'departments': departments,
        # Статистика
        'total_events': total_events,
        'filtered_count': events.count(),
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


def get_filtered_event_ids(request):
    """Возвращает все ID мероприятий, соответствующих текущим фильтрам"""
    try:
        # Получаем параметры фильтрации (такие же как в events_ui)
        month_str = request.GET.get('month', '')
        year_str = request.GET.get('year', '')
        category_id = request.GET.get('category', '')
        department_id = request.GET.get('department', '')
        search_query = request.GET.get('search', '')
        start_date_str = request.GET.get('start_date', '')
        end_date_str = request.GET.get('end_date', '')

        # Базовый queryset
        events = Event.objects.all()

        # Повторяем ВСЮ логику фильтрации из events_ui:

        # ФИЛЬТРАЦИЯ ПО МЕСЯЦУ И ГОДУ
        month_int = None
        year_int = None

        if month_str and month_str.strip() and month_str != 'None':
            try:
                month_int = int(month_str)
                if not (1 <= month_int <= 12):
                    month_int = None
            except (ValueError, TypeError):
                pass

        if year_str and year_str.strip() and year_str != 'None':
            try:
                year_int = int(year_str)
            except (ValueError, TypeError):
                year_int = None

        if month_int and year_int:
            events = events.filter(
                Q(date__month=month_int, date__year=year_int) |
                Q(end_date__month=month_int, end_date__year=year_int)
            )
        elif year_int:
            events = events.filter(
                Q(date__year=year_int) | Q(end_date__year=year_int)
            )
        elif month_int:
            current_year_for_filter = dt.now().year
            events = events.filter(
                Q(date__month=month_int, date__year=current_year_for_filter) |
                Q(end_date__month=month_int, end_date__year=current_year_for_filter)
            )

        # Фильтрация по категории
        if category_id and category_id != '':
            try:
                category_int = int(category_id)
                events = events.filter(category_id=category_int)
            except ValueError:
                pass

        # Фильтрация по подразделению
        if department_id and department_id != '':
            try:
                department_int = int(department_id)
                events = events.filter(department_id=department_int)
            except ValueError:
                pass

        # Фильтрация по диапазону дат
        if start_date_str or end_date_str:
            if start_date_str:
                try:
                    start_date = dt.strptime(start_date_str, '%Y-%m-%d')
                    start_datetime = timezone.make_aware(start_date)
                    events = events.filter(
                        Q(date__gte=start_datetime) |
                        Q(end_date__gte=start_datetime) |
                        Q(date__lte=start_datetime, end_date__gte=start_datetime)
                    )
                except ValueError:
                    pass

            if end_date_str:
                try:
                    end_date = dt.strptime(end_date_str, '%Y-%m-%d')
                    end_date = end_date.replace(hour=23, minute=59, second=59)
                    end_datetime = timezone.make_aware(end_date)
                    events = events.filter(
                        Q(date__lte=end_datetime) |
                        Q(end_date__lte=end_datetime) |
                        Q(date__lte=end_datetime, end_date__gte=end_datetime)
                    )
                except ValueError:
                    pass

        # Поиск по тексту
        if search_query:
            search_terms = search_query.split()
            search_q = Q()

            for term in search_terms:
                search_q |= (
                        Q(name__icontains=term) |
                        Q(place__icontains=term) |
                        Q(comment__icontains=term) |
                        Q(responsible__icontains=term) |
                        Q(category__name__icontains=term) |
                        Q(department__name__icontains=term)
                )

            events = events.filter(search_q)

        # Получаем только ID
        event_ids = list(events.values_list('id', flat=True))

        return JsonResponse({
            'event_ids': event_ids,
            'count': len(event_ids),
            'success': True
        })

    except Exception as e:
        return JsonResponse({
            'event_ids': [],
            'count': 0,
            'success': False,
            'error': str(e)
        }, status=500)