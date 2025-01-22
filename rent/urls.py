from django.urls import path

from .admin import revenue_report
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('revenue-report/', revenue_report, name='revenue_report'),
]
