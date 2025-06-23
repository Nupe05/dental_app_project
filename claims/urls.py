from django.urls import path
from . import views

urlpatterns = [
    path('recommend/', views.create_crown_recommendation, name='create_recommendation'),
    path('success/', views.recommendation_success, name='recommendation_success'),
    path('pdf/<int:recommendation_id>/', views.generate_pdf, name='generate_pdf'),
    path('pms/', views.pms_home, name='pms_home'),
    path('pms/patient/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    path('pms/patient/<int:patient_id>/tooth/<int:tooth_id>/add/', views.add_crown_treatment, name='add_crown'),
    path('pms/success/', views.pms_success, name='pms_success'),

]
