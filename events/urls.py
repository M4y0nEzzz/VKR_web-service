from django.urls import path
from . import views

urlpatterns = [
    path('events/ui/', views.events_ui, name='events_ui'),
    path('events/export/', views.export_selected_events, name='export_selected_events'),
]