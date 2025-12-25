from django.urls import path
from . import views

urlpatterns = [
    path('', views.payroll_list, name='payroll_list'),
    path('create/', views.payroll_create, name='payroll_create'),
    path('logout/', views.logout_view, name='logout'),
    
    # Employee management
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/create/', views.employee_create, name='employee_create'),
    path('employees/<str:employee_id>/edit/', views.employee_edit, name='employee_edit'),
    path('employees/<str:employee_id>/delete/', views.employee_delete, name='employee_delete'),
    
    # Payroll detail and downloads
    path('<str:run_id>/', views.payroll_detail, name='payroll_detail'),
    path('<str:run_id>/lines/<str:line_id>/deductions/', views.get_deductions, name='get_deductions'),
    path('<str:run_id>/lines/<str:line_id>/deductions/save/', views.save_deductions, name='save_deductions'),
    path('<str:run_id>/download/', views.download_payroll_pdf, name='download_payroll_pdf'),
    path('<str:run_id>/download-zip/', views.download_all_payslips_zip, name='download_all_payslips_zip'),
    path('<str:run_id>/lines/<str:line_id>/download/', views.download_single_payslip, name='download_single_payslip'),
]