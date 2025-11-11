from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'mentor'
urlpatterns = [
    path('', views.home, name='home'),
    path('form/', views.career_form, name='career_form'),
    path('predict/', views.predict, name='predict'),

    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('history/', views.history_view, name='history'),
    path("history/", views.history_view, name="history"),
    path("history/delete/<int:pk>/", views.delete_history, name="delete_history"),
    path("history/delete_all/", views.delete_history, name="delete_all_history"),
    path("chat/api/", views.chat_api, name="chat_api"),  
    path("chat/", views.chat_page, name="chat_page"), 

    # PDF
    path('pdf/<int:pk>/', views.export_pdf, name='export_pdf'),
        path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='password_reset.html'), 
         name='password_reset'),

    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), 
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), 
         name='password_reset_confirm'),

    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), 
         name='password_reset_complete'),

]
