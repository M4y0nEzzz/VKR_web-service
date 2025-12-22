from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('events/ui/', views.events_ui, name='events_ui'),
    path('events/export/', views.export_selected_events, name='export_selected_events'),
    path('create/', views.create_event, name='create_event'),
    path('edit/<int:event_id>/', views.edit_event, name='edit_event'),
    path('delete/<int:event_id>/', views.delete_event, name='delete_event'),
    path('bulk-delete/', views.bulk_delete_events, name='bulk_delete_events'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('check-db/', views.check_database, name='check_database'),
    path('get-filtered-ids/', views.get_filtered_event_ids, name='get_filtered_event_ids'),
]