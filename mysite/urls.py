from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from hrm.views import dashboard
from manualentry.views import DashboardView  # ড্যাশবোর্ড ভিউ ইমপোর্ট
 
urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='mainsystem/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # App Sections
    path('mainsystem/', include('mainsystem.urls')),
    path('hrm/', include('hrm.urls')),
    #path('attendance/', include('attendance.urls')),
    path('', DashboardView.as_view(), name='dashboard'),
    path('manual-entry/', include('manualentry.urls')),
    #path('', dashboard, name='dashboard'), 
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)