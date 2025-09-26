from django.urls import path
from . import views

urlpatterns = [
    path('generate-leads/', views.generate_leads, name='generate_leads'),
]