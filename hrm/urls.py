from django.urls import path
from . import views

app_name = 'hrm'

urlpatterns = [
    # Staff Profiles
    path('dashboard/', views.dashboard_api, name='dashboard_api'),
    path('staff/', views.staff_list, name='staff_list'),
    path('get-staff-data/<int:id>/', views.get_staff_data, name='get_staff_data'),
    path('staff/create/', views.profile_view_or_edit, name='staff_create'), # reuse your profile view
    path('staff/view/<int:id>/', views.staff_biodata, name='staff_biodata'),
    path('staff/report/', views.staff_report, name='staff_report'),
    path('staff/id-card/<int:staff_id>/', views.single_id_card, name='single_id_card'),    
    # Department Management
    #path('departments/', views.add_department, name='department_list'),
    path('departments/add/', views.add_department, name='add_department'),
    path('departments/edit/<int:pk>/', views.edit_department, name='edit_department'),
    path('departments/delete/<int:pk>/', views.delete_department, name='delete_department'),
    path('api/departments-json/', views.department_list_json, name='department_list_json'),

    # Leave Requests (ছুটির আবেদন)
    path('leaves/', views.leave_list, name='leave_list'),
    path('leaves/create/', views.leave_create, name='leave_create'),
    path('leaves/<int:id>/edit/', views.leave_edit, name='leave_edit'),
    path('leaves/<int:id>/approve/', views.leave_approve, name='leave_approve'),
    path('leaves/<int:id>/reject/', views.leave_reject, name='leave_reject'), # রিজেক্ট করার অপশন
    
    # Public Holidays (সরকারি ছুটি)
    path('holidays/', views.holiday_list, name='holiday_list'),
    path('holidays/create/', views.holiday_create, name='holiday_create'),
    path('holidays/<int:id>/delete/', views.holiday_delete, name='holiday_delete'),
]