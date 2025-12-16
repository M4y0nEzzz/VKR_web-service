from django import forms
from django.forms import formset_factory
from .models import Event


class EventBaseForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = (
            "title",
            "category",
            "department",
            "responsibles",
            "locations",
            "description",
            "is_published",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "responsibles": forms.SelectMultiple(),
            "locations": forms.SelectMultiple(),
        }


class EventDateForm(forms.Form):
    date_start = forms.DateTimeField(
        label="Начало",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )
    date_end = forms.DateTimeField(
        label="Окончание",
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )


EventDateFormSet = formset_factory(
    EventDateForm,
    extra=1,
    can_delete=True,
)
