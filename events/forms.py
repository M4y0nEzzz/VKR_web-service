from django import forms
from .models import Event
from categories.models import Category
from departments.models import Department
from users.models import User

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'date', 'end_date', 'place', 'category', 'department', 'responsible', 'comment']

    responsible = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Имя ответственного, через запятую'}))