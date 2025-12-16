from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect
from django.urls import reverse

from categories.models import Category
from departments.models import Department
from locations.models import Location
from users.models import User

from .forms import EventBaseForm, EventDateFormSet
from .models import Event


def _is_admin(user) -> bool:
    return user.groups.filter(name="admin").exists()


def _is_department_head(user) -> bool:
    return user.groups.filter(name="department_head").exists()


def _events_for_user(user):
    qs = Event.objects.all().select_related("category", "department", "created_by").prefetch_related("responsibles", "locations")

    if _is_admin(user):
        return qs

    if _is_department_head(user):
        # если department не задан, то хотя бы свои
        if getattr(user, "department_id", None):
            return qs.filter(department_id=user.department_id) | qs.filter(created_by_id=user.id)
        return qs.filter(created_by_id=user.id)

    return qs.filter(created_by_id=user.id)


@login_required
def event_list(request):
    events = _events_for_user(request.user).order_by("-date_start")
    return render(request, "list.html", {"events": events})


@login_required
def event_create(request):
    if request.method == "POST":
        form = EventBaseForm(
            request.POST,
            Category=Category,
            Department=Department,
            UserModel=User,
            Location=Location,
        )
        formset = EventDateFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            # Проверим, что есть хотя бы одна "живая" дата
            has_any = False
            for df in formset:
                if df.cleaned_data and not df.cleaned_data.get("DELETE", False):
                    has_any = True
                    break

            if not has_any:
                formset.non_form_errors = lambda: ["Добавьте хотя бы одну дату проведения."]
                return render(request, "form.html", {"form": form, "formset": formset})

            with transaction.atomic():
                for df in formset:
                    if not df.cleaned_data or df.cleaned_data.get("DELETE", False):
                        continue

                    event = Event.objects.create(
                        title=form.cleaned_data["title"],
                        category=form.cleaned_data["category"],
                        department=form.cleaned_data["department"],
                        description=form.cleaned_data.get("description") or "",
                        is_published=bool(form.cleaned_data.get("is_published")),
                        date_start=df.cleaned_data["date_start"],
                        date_end=df.cleaned_data.get("date_end"),
                        created_by=request.user,
                    )

                    # ВАЖНО: M2M применяем к КОНКРЕТНОМУ событию
                    event.responsibles.set(form.cleaned_data["responsibles"])
                    event.locations.set(form.cleaned_data["locations"])

            return redirect(reverse("events:event_list"))

    else:
        form = EventBaseForm(
            Category=Category,
            Department=Department,
            UserModel=User,
            Location=Location,
        )
        formset = EventDateFormSet()

    return render(request, "form.html", {"form": form, "formset": formset})
