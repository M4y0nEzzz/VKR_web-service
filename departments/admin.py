from django.contrib import admin
from django.utils.html import format_html
from django.utils.formats import date_format
from django import forms
from .models import Department

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = "__all__"
        widgets = {
            'name': forms.TextInput(attrs={'class': 'mc-input', 'placeholder': 'Название подразделения'}),
            'description': forms.Textarea(attrs={'class': 'mc-textarea', 'rows': 4, 'placeholder': 'Описание подразделения'}),
        }


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("card",)
    list_display_links = ("card",)
    search_fields = ("name", "description")
    list_per_page = 30

    def card(self, obj: Department):
        desc = (getattr(obj, "description", "") or "—").replace("\n", "<br/>")
        events_count = obj.event_set.count() if hasattr(obj, "event_set") else 0
        users_count = obj.user_set.count() if hasattr(obj, "user_set") else 0

        return format_html(
            '''
            <div class="mc-card">
              <div class="mc-head">
                <span class="mc-id">#{id}</span>
                <h2 class="mc-title">{name}</h2>
              </div>

              <div class="mc-grid">
                <div class="mc-box"><div class="mc-label">Мероприятий</div><p class="mc-val">{events_count}</p></div>
                <div class="mc-box"><div class="mc-label">Пользователей</div><p class="mc-val">{users_count}</p></div>
              </div>

              <div class="mc-box" style="margin-top:12px">
                <div class="mc-label">Описание</div>
                <div class="mc-prose">{desc}</div>
              </div>

              <div class="mc-meta">
                <div>Создано: {created}</div><div>Обновлено: {updated}</div>
              </div>
            </div>
            ''',
            id=obj.pk, name=obj.name, slug=(getattr(obj, "slug", "—") or "—"),
            events_count=events_count, users_count=users_count, desc=desc,
            created=(date_format(getattr(obj, "created_at", None), "j E Y в H:i") if getattr(obj, "created_at",
                                                                                             None) else "—"),
            updated=(date_format(getattr(obj, "updated_at", None), "j E Y в H:i") if getattr(obj, "updated_at",
                                                                                             None) else "—"),
        )

    card.short_description = "Подразделение"

    class Media:
        css = {"all": ("departments/admin-card.css",)}