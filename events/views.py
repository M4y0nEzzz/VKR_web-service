from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect

from .forms import EventBaseForm, EventDateFormSet
from .models import Event
from .permissions import can_view_event


@login_required
def event_list(request):
    events = Event.objects.all()
    events = [e for e in events if can_view_event(request.user, e)]

    return render(
        request,
        "events/event_list.html",
        {"events": events},
    )


@login_required
def event_create(request):
    if request.method == "POST":
        form = EventBaseForm(request.POST)
        formset = EventDateFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                for date_form in formset:
                    if not date_form.cleaned_data:
                        continue
                    if date_form.cleaned_data.get("DELETE"):
                        continue

                    event = form.save(commit=False)
                    event.date_start = date_form.cleaned_data["date_start"]
                    event.date_end = date_form.cleaned_data.get("date_end")
                    event.created_by = request.user
                    event.save()

                    # сохранение M2M (responsibles, locations)
                    form.save_m2m()

            return redirect("events:list")

    else:
        form = EventBaseForm()
        formset = EventDateFormSet()

    return render(
        request,
        "events/event_form.html",
        {
            "form": form,
            "formset": formset,
        },
    )
