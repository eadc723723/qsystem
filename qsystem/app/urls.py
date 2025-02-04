#urls.py
from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('select_activity/', views.select_activity, name='select_activity'),
    path('queue_number/<int:activity_id>/', views.queue_number, name='queue_number'),
    path('queue_number_display/<int:queue_number_id>/', views.queue_number_display, name='queue_number_display'),
    path('queue/reset/', views.reset_queue_number, name='reset_queue_number'),
    path('staff_sign_in/', views.staff_sign_in, name='staff_sign_in'),
    path('staff_dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('reinforce_called_numbers/', views.reinforce_called_numbers, name='reinforce_called_numbers'),
    path('update_queue_status/', views.update_queue_status, name='update_queue_status'),
    path('get_queue_numbers/', views.get_queue_numbers, name='get_queue_numbers'),
    path('sign_out_and_log_out/', views.sign_out_and_log_out, name='sign_out_and_log_out'),
    path('login/', views.user_login, name='login'),
    path('ajax-sign-out/', views.ajax_sign_out, name='ajax_sign_out'),
    path('logout/', LogoutView.as_view(next_page='/login/'), name='logout'),
    path('get_current_queue_info/', views.get_current_queue_info, name='get_current_queue_info'),
    path('monitor_display/', views.monitor_display, name='monitor_display'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)