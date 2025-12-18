from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('events/ui/', views.events_ui, name='events_ui'),
    path('events/export/', views.export_selected_events, name='export_selected_events'),
    path('create/', views.create_event, name='create_event'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]