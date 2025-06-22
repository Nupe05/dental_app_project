from django.urls import path
from . import views

urlpatterns = [
    path('recommend/', views.create_crown_recommendation, name='create_recommendation'),
    path('success/', views.recommendation_success, name='recommendation_success'),
    path('pdf/<int:recommendation_id>/', views.generate_pdf, name='generate_pdf'),
]
