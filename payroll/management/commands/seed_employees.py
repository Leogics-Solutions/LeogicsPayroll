from django.core.management.base import BaseCommand
from payroll_mvp.firebase import db

class Command(BaseCommand):
    help = 'Seed test employees into Firestore'

    def handle(self, *args, **kwargs):
        employees = [
            {
                'name': 'John Tan',
                'role': 'Software Engineer',
                'nationality': 'Malaysian',
                'employee_id': 'EMP001',
                'passport': 'A12345678',
                'epf_no': 'EPF123456',
                'socso_no': 'SOCSO123456',
                'gender': 'Male',
                'base_salary': 5500,
                # Statutory deductions
                'epf_deduction': 605.00,    # 11% of salary
                'socso_deduction': 24.50,
                'eis_deduction': 8.25,
                'zakat_deduction': 0.00,
                'pcb_deduction': 150.00,
                'hrdf_deduction': 5.50
            },
            {
                'name': 'Sarah Lim',
                'role': 'Product Manager',
                'nationality': 'Malaysian',
                'employee_id': 'EMP002',
                'passport': 'B98765432',
                'epf_no': 'EPF789012',
                'socso_no': 'SOCSO789012',
                'gender': 'Female',
                'base_salary': 7200,
                'epf_deduction': 792.00,
                'socso_deduction': 24.50,
                'eis_deduction': 10.80,
                'zakat_deduction': 144.00,  # 2% for zakat
                'pcb_deduction': 250.00,
                'hrdf_deduction': 7.20
            },
            {
                'name': 'Ahmad Ibrahim',
                'role': 'UI/UX Designer',
                'nationality': 'Malaysian',
                'employee_id': 'EMP003',
                'passport': 'C11223344',
                'epf_no': 'EPF345678',
                'socso_no': 'SOCSO345678',
                'gender': 'Male',
                'base_salary': 4800,
                'epf_deduction': 528.00,
                'socso_deduction': 24.50,
                'eis_deduction': 7.20,
                'zakat_deduction': 0.00,
                'pcb_deduction': 80.00,
                'hrdf_deduction': 4.80
            },
            {
                'name': 'Michelle Wong',
                'role': 'HR Manager',
                'nationality': 'Malaysian',
                'employee_id': 'EMP004',
                'passport': 'D55667788',
                'epf_no': 'EPF901234',
                'socso_no': 'SOCSO901234',
                'gender': 'Female',
                'base_salary': 6000,
                'epf_deduction': 660.00,
                'socso_deduction': 24.50,
                'eis_deduction': 9.00,
                'zakat_deduction': 0.00,
                'pcb_deduction': 180.00,
                'hrdf_deduction': 6.00
            }
        ]

        # Delete existing employees first
        existing = db.collection('employees').stream()
        for doc in existing:
            doc.reference.delete()
        
        # Add new employees
        for emp in employees:
            db.collection('employees').add(emp)
            self.stdout.write(self.style.SUCCESS(f'Added employee: {emp["name"]}'))

        self.stdout.write(self.style.SUCCESS('\nSuccessfully seeded 4 employees with statutory deductions!'))