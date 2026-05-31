from django.urls import path
from . import views

app_name = 'mainsystem'

urlpatterns = [
    # 🛡️ Role Management
    path('roles/', views.role_list, name='role_list'),
    path('roles/create/', views.role_form, name='role_create'),
    path('roles/edit/<int:role_id>/', views.role_form, name='role_edit'),
    path('roles/delete/<int:role_id>/', views.role_delete, name='role_delete'),
    path('roles/clone/<int:source_role_id>/', views.role_clone_view, name='role_clone'),    

    # 🛡️ Permission Management
    path('permissions/matrix/', views.permission_matrix_view, name='permission_matrix'),
    path('permissions/update/', views.update_permission, name='update_permission'),
    path('permissions/grant_all/', views.grant_all_permissions_view, name='grant_all_permissions'),
    path('permissions/revoke_all/', views.revoke_all_permissions_view, name='revoke_all_permissions'),

    # 👤 User Management
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_form_handler, name='user_create'),
    path('users/edit/<int:user_id>/', views.user_form_handler, name='user_edit'),
    path('users/delete/<int:user_id>/', views.user_delete, name='user_delete'),
    path('password-modal/', views.password_modal_view, name='password_modal'),
    path('users/password/<int:user_id>/', views.user_password_update, name='user_password_update'),

    # 📁 Profile & Department Management
    #path('profile/<int:user_id>/', views.profile_view_or_edit, name='profile_view'),
    #path('departments/add1/', views.manage_department_ajax, name='manage_department_ajax'),
    #path('departments/add/', views.add_department, name='add_department'),
    #path('departments/edit/<int:pk>/', views.edit_department, name='edit_department'),
    #path('departments/delete/<int:pk>/', views.delete_department, name='delete_department'),
    #path('departments/list-json/', views.department_list_json, name='department_list_json'),

    # 📦 Module Management
    path('modules/sync/ajax/', views.sync_modules_ajax, name='module_sync'),
    path('modules/', views.module_list, name='module_list'),
    path('modules/form/', views.module_form_handler, name='module_create'),
    path('modules/form/<int:module_id>/', views.module_form_handler, name='module_update'),
    path('modules/delete/<int:module_id>/', views.module_delete, name='module_delete'),
    
    # 🗂️ ModuleGroup Management    
    path('module-groups/', views.module_group_list_view, name='module_group_list'),
    path('module-groups/save/', views.module_group_save_ajax, name='module_group_save'),
    path('module-groups/delete/<int:id>/', views.module_group_delete_ajax, name='module_group_delete'),
]