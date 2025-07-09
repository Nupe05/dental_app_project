from django.urls import path
from . import views
from .views import CustomLoginView

urlpatterns = [
    path('recommend/', views.create_crown_recommendation, name='create_recommendation'),
    path('success/', views.recommendation_success, name='recommendation_success'),
    path('pms/', views.pms_home, name='pms_home'),
    path('pms/patient/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    path('pms/patient/<int:patient_id>/tooth/<int:tooth_id>/add/', views.add_crown_treatment, name='add_crown'),
    path('pms/success/', views.pms_success, name='pms_success'),
    path('pms/patient/<int:patient_id>/srp/', views.submit_srp_treatment, name='submit_srp'),
    path('pms/patient/<int:patient_id>/occlusal_guard/', views.submit_occlusal_guard, name='submit_occlusal_guard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.custom_logout, name='logout'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('pms/patients/', views.patient_list, name='patient_list'),
    path('pms/patient/<int:patient_id>/xray/', views.take_xray, name='take_xray'),
    path('pms/patient/<int:patient_id>/test_model/', views.test_model_view, name='test_model'),
    path('pdf/crown/<int:recommendation_id>/', views.generate_crown_pdf, name='generate_crown_pdf'),
    path('pdf/treatment/<int:treatment_id>/', views.generate_treatment_pdf, name='generate_treatment_pdf'),

    
]
