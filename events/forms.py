from django import forms
from django.forms import formset_factory


class EventBaseForm(forms.Form):
    title = forms.CharField(label="Название", max_length=500)
    category = forms.ModelChoiceField(label="Категория", queryset=None)
    department = forms.ModelChoiceField(label="Подразделение", queryset=None)

    responsibles = forms.ModelMultipleChoiceField(
        label="Ответственные",
        queryset=None,
        required=False,
        widget=forms.SelectMultiple(),
    )
    locations = forms.ModelMultipleChoiceField(
        label="Места проведения",
        queryset=None,
        required=False,
        widget=forms.SelectMultiple(),
    )

    description = forms.CharField(
        label="Комментарий",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    is_published = forms.BooleanField(
        label="Опубликовать на сайте университета",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        Category = kwargs.pop("Category")
        Department = kwargs.pop("Department")
        UserModel = kwargs.pop("UserModel")
        Location = kwargs.pop("Location")
        super().__init__(*args, **kwargs)

        self.fields["category"].queryset = Category.objects.all()
        self.fields["department"].queryset = Department.objects.all()
        self.fields["responsibles"].queryset = UserModel.objects.all()
        self.fields["locations"].queryset = Location.objects.all()


class EventDateForm(forms.Form):
    date_start = forms.DateTimeField(
        label="Начало",
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )
    date_end = forms.DateTimeField(
        label="Окончание",
        required=False,
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("date_start")
        end = cleaned.get("date_end")
        if start and end and end < start:
            raise forms.ValidationError("Окончание не может быть раньше начала.")
        return cleaned


EventDateFormSet = formset_factory(
    EventDateForm,
    extra=1,
    can_delete=True,
)
