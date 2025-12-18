from django.contrib import admin
from django.utils.html import format_html
from django.utils.formats import date_format
from django import forms
from .models import Location

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = "__all__"
        widgets = {
            'name': forms.TextInput(attrs={'class': 'mc-input', 'placeholder': 'Название места'}),
            'address': forms.TextInput(attrs={'class': 'mc-input', 'placeholder': 'Адрес'}),
            'description': forms.Textarea(attrs={'class': 'mc-textarea', 'rows': 4, 'placeholder': 'Описание места'}),
        }


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("card",)
    list_display_links = ("card",)
    search_fields = ("name", "address", "description")
    list_per_page = 30

    def card(self, obj: Location):
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
                <div class="mc-box"><div class="mc-label">Адрес</div><p class="mc-val">{address}</p></div>
                <div class="mc-box"><div class="mc-label">Мероприятий</div><p class="mc-val">{events_count}</p></div>
              </div>
            </div>
            ''',
            id=obj.pk, name=obj.name, address=(obj.address or "—"),
            events_count=events_count, desc=desc,
            created=(date_format(getattr(obj, "created_at", None), "j E Y в H:i") if getattr(obj, "created_at",
                                                                                             None) else "—"),
            updated=(date_format(getattr(obj, "updated_at", None), "j E Y в H:i") if getattr(obj, "updated_at",
                                                                                             None) else "—"),
        )

    card.short_description = "Место проведения"

    class Media:
        css = {"all": ("locations/admin-card.css",)}