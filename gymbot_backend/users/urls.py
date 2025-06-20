from django.urls import path, include
from . import views  
from django.contrib.auth import views as auth_views
from .views import api_login_view
from .views import (
    RegisterView, LoginView, logout_view, home,
    protected_view, ProfileView, ProfileDetailView,
    user_list, admin_panel, admin_panel_view,
    chat_with_gemini, update_user_info, calendar_view,
    toggle_done, delete_plan, delete_all_plans,
    update_language , forgot_password_view ,reset_password_confirm_view
)
urlpatterns = [
    path('', home, name='home'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('protected/', protected_view, name='protected'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile-detail/', ProfileDetailView.as_view(), name='profile_detail'),
    path('list/', user_list, name='user_list'),
    path('admin-panel/', admin_panel_view, name='admin_panel'),
    path('chat/gemini/', chat_with_gemini, name='chat_with_gemini'),
    path('update-info/', update_user_info, name='update_user_info'),
    path('calendar/', calendar_view, name='calendar'),
    path('plan/done/<int:plan_id>/', toggle_done, name='toggle_done'),
    path('plan/delete/<int:plan_id>/', delete_plan, name='delete_plan'),
    path('plan/delete_all/', delete_all_plans, name='delete_all_plans'),
    path('set-language/', update_language, name='set_language'),
    path('api/calendar/json/', views.calendar_json, name='calendar_json'),
    path('api/users/login/', api_login_view),

    #  ADMIN YETKİLİ İŞLEMLER
    path("admin/users/<int:user_id>/", views.admin_update_user, name="admin_update_user"),

    path("admin/users/<int:user_id>/delete/", views.admin_delete_user, name="admin_delete_user"),

     #  CAPTCHA URL EKLENTİSİ
    path('captcha/', include('captcha.urls')),

    path("forgot-password/", forgot_password_view, name="forgot_password"),
    
    path("reset-password-confirm/<uidb64>/<token>/", reset_password_confirm_view, name="reset_password_confirm"),

]
  
  


