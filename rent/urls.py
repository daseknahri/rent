from django.urls import path

from .admin import revenue_report
from . import views

urlpatterns = [
    path('', views.register, name='register'),
    path('thank-you/', views.thank_you, name='thank_you'),
    #path('', views.home, name='home'),
    #path('jewlery/', views.test, name='home'),
    path('revenue-report/', revenue_report, name='revenue_report'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('api/get-car-daily-rate/', views.get_car_daily_rate, name="get_car_daily_rate"),

]
