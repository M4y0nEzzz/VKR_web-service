from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db.models.functions import ExtractMonth, ExtractYear
import openpyxl
from io import BytesIO
from django.views.decorators.csrf import csrf_exempt
from openpyxl.styles import Alignment
from .models import Event
from .forms import EventForm


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
                # Преобразуем строки в числа
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

    return redirect('events_ui')



def events_ui(request):
    month = request.GET.get('month')
    year = request.GET.get('year')
    sort_order = request.GET.get('sort_order', 'asc')

    events = Event.objects.all()

    if month:
        try:
            month = int(month)
        except ValueError:
            month = None

    if year:
        try:
            year = int(year)
        except ValueError:
            year = None

    if month:
        events = events.annotate(month=ExtractMonth('date')).filter(month=month)

    if year:
        events = events.annotate(year=ExtractYear('date')).filter(year=year)

    if sort_order == 'desc':
        events = events.order_by('-date')
    else:
        events = events.order_by('date')



    paginator = Paginator(events, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    for event in page_obj:
        if event.responsible:
            event.responsible_list = event.responsible.split(',')
        else:
            event.responsible_list = []

    return render(
        request,
        'events/eventsUI.html',
        {'page_obj': page_obj, 'month': month, 'year': year, 'sort_order': sort_order}
    )


@csrf_exempt
def export_selected_events(request):
    if request.method == "POST":
        selected_event_ids = request.POST.getlist('selected_events')

        if not selected_event_ids:
            return HttpResponse("Не выбраны мероприятия для экспорта.", status=400)

        events = Event.objects.filter(id__in=selected_event_ids)

        if not events:
            return HttpResponse("Не удалось найти выбранные мероприятия.", status=400)

        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = "План мероприятий"

        headers = [
            "№", "Название мероприятия", "Дата начала", "Дата окончания", "Категория",
            "Подразделение", "Ответственные", "Место проведения", "Комментарий"
        ]

        for col_num, header in enumerate(headers, 1):
            worksheet.cell(row=1, column=col_num, value=header)

        for col_num in range(1, len(headers) + 1):
            worksheet.cell(row=1, column=col_num).alignment = Alignment(horizontal='center', vertical='center')

        row_num = 5
        for idx, event in enumerate(events, start=1):
            responsible_names = event.responsible
            worksheet.cell(row=row_num, column=1, value=idx)
            worksheet.cell(row=row_num, column=2, value=event.name)
            worksheet.cell(row=row_num, column=3,
                           value=event.date.strftime('%d-%m-%Y %H:%M') if event.date else "")
            worksheet.cell(row=row_num, column=4,
                           value=event.end_date.strftime('%d-%m-%Y %H:%M') if event.end_date else "")
            worksheet.cell(row=row_num, column=5, value=event.category.name if event.category else "")
            worksheet.cell(row=row_num, column=6,
                           value=event.department.name if event.department else "")
            worksheet.cell(row=row_num, column=7, value=responsible_names or "")
            worksheet.cell(row=row_num, column=8, value=event.place)
            worksheet.cell(row=row_num, column=9, value=event.comment)

            row_num += 1

        for row in worksheet.iter_rows(min_row=2, min_col=1, max_col=9, max_row=row_num - 1):
            for cell in row:
                cell.alignment = Alignment(horizontal='left', vertical='center')

        output = BytesIO()
        workbook.save(output)
        output.seek(0)

        response = HttpResponse(
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response['Content-Disposition'] = 'attachment; filename="events_export.xlsx"'
        return response
