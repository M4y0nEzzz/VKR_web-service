from django.contrib import admin
from django.utils.html import format_html
from django.utils.formats import date_format
from django import forms
from .models import Category


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description", "color"]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'mc-input', 'placeholder': 'Название категории'}),
            'description': forms.Textarea(attrs={'class': 'mc-textarea', 'rows': 4, 'placeholder': 'Описание категории'}),
            'color': forms.TextInput(attrs={'class': 'mc-input', 'placeholder': 'Цвет метки (HEX)', 'type': 'color'}),
        }


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("card",)  # Отображаем только карточку
    list_display_links = ("card",)  # Карточка будет ссылкой
    search_fields = ("name",)  # Добавляем поиск по полю name
    list_per_page = 30  # Количество категорий на одной странице

    def card(self, obj: Category):
        desc = (getattr(obj, "description", "") or "—").replace("\n", "<br/>")
        events_count = obj.event_set.count() if hasattr(obj, "event_set") else 0

        return format_html(
            '''
            <div class="mc-card">
              <div class="mc-head">
                <span class="mc-id">#{id}</span>
                <h2 class="mc-title">{name}</h2>
              </div>

              <div class="mc-grid">
                
                <div class="mc-box"><div class="mc-label">Мероприятий</div><p class="mc-val">{events_count}</p></div>
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
            events_count=events_count, desc=desc,
            created=(date_format(getattr(obj, "created_at", None), "j E Y в H:i") if getattr(obj, "created_at",
                                                                                             None) else "—"),
            updated=(date_format(getattr(obj, "updated_at", None), "j E Y в H:i") if getattr(obj, "updated_at",
                                                                                             None) else "—"),
        )

    card.short_description = "Категория"

    class Media:
        css = {"all": ("categories/admin-card.css",)}