from django.contrib import admin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("card",)
    list_display_links = ("card",)
    list_per_page = 30
    search_fields = ("name", "displayname", "role",
                     "department__name")
    list_filter = ("role", "department")

    class Media:
        css = {"all": ("events/admin-card.css",)}

    def card(self, obj: User):
        return format_html(
            """
            <div class="mc-card">
              <div class="mc-head">
                <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
                  <span class="mc-id">#{id}</span>
                  <h2 class="mc-title">{title}</h2>
                </div>
              </div>

              <div class="mc-grid">
                <div class="mc-box"><div class="mc-label">Имя</div><p class="mc-val">{name}</p></div>
                <div class="mc-box"><div class="mc-label">Отображаемое имя</div><p class="mc-val">{displayname}</p></div>
                <div class="mc-box"><div class="mc-label">Роль</div><p class="mc-val">{role}</p></div>
                <div class="mc-box"><div class="mc-label">Подразделение</div><p class="mc-val">{department}</p></div>
              </div>
            </div>
            """,
            id=obj.pk,
            title=obj.displayname or obj.name or f"User #{obj.pk}",
            name=obj.name or "—",
            displayname=obj.displayname or "—",
            role=obj.role or "—",
            department=(getattr(obj.department, "name", "—") if obj.department else "—"),
        )

    card.short_description = "Пользователь"
