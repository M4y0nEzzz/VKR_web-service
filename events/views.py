from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Event
from django.contrib import messages

# Просмотр списка всех мероприятий
def event_list(request):
    events = Event.objects.all()  # Получаем все мероприятия из базы данных
    return render(request, 'events/event_list.html', {'events': events})

# Страница для создания нового мероприятия (будет использовать стандартную форму Django)
def create_event(request):
    if request.method == 'POST':
        event = Event(
            name=request.POST.get('name'),
            date=request.POST.get('date'),
            end_date=request.POST.get('end_date'),
            place=request.POST.get('place'),
            category_id=request.POST.get('category'),
            department_id=request.POST.get('department'),
            responsible=request.POST.getlist('responsible'),
            comment=request.POST.get('comment')
        )
        event.save()  # Сохраняем новое мероприятие
        messages.success(request, 'Мероприятие успешно добавлено!')
        return redirect('event_list')  # Перенаправляем на страницу со списком мероприятий
    return render(request, 'events/create_event.html')

# Просмотр конкретного мероприятия
def event_detail(request, pk):
    event = Event.objects.get(pk=pk)  # Получаем конкретное мероприятие по его ID
    return render(request, 'events/event_detail.html', {'event': event})

# Страница для редактирования мероприятия
def edit_event(request, pk):
    event = Event.objects.get(pk=pk)
    if request.method == 'POST':
        event.name = request.POST.get('name')
        event.date = request.POST.get('date')
        event.end_date = request.POST.get('end_date')
        event.place = request.POST.get('place')
        event.category_id = request.POST.get('category')
        event.department_id = request.POST.get('department')
        event.responsible = request.POST.getlist('responsible')
        event.comment = request.POST.get('comment')
        event.save()  # Сохраняем изменения
        messages.success(request, 'Мероприятие обновлено!')
        return redirect('event_list')  # Перенаправляем на страницу со списком мероприятий
    return render(request, 'events/edit_event.html', {'event': event})

# Экспорт мероприятий в Excel
def export_events_to_excel(request):
    from io import BytesIO
    import openpyxl

    # Создание файла Excel
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

    # Сохранение файла в ответе
    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response['Content-Disposition'] = 'attachment; filename="events_export.xlsx"'
    return response
