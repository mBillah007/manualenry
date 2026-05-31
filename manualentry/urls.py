from django.urls import path
from . import views

app_name = 'manualentry'

urlpatterns = [
    # --- Terminal Registry Routes ---
    path('terminals/', views.TerminalListView.as_view(), name='terminal_list'),
    path('terminals/add/', views.TerminalCreateView.as_view(), name='terminal_add'),
    path('terminals/<int:pk>/edit/', views.TerminalUpdateView.as_view(), name='terminal_edit'),
    path('terminals/<int:pk>/delete/', views.TerminalDeleteView.as_view(), name='terminal_delete'),

    # --- Manual Entry Dataset Logs Routes ---
    path('manual-entry/', views.EntryListView.as_view(), name='entry_list'),
    path('manual-entry/add/', views.EntryCreateView.as_view(), name='entry_add'),
    path('manual-entry/<int:pk>/edit/', views.EntryUpdateView.as_view(), name='entry_edit'),
    path('manual-entry/<int:pk>/delete/', views.EntryDeleteView.as_view(), name='entry_delete'),
]