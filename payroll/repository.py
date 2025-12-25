from payroll_mvp.firebase import db
from datetime import datetime

# === EMPLOYEES ===

def get_all_employees():
    """Get all employees from Firestore"""
    employees = []
    docs = db.collection('employees').stream()
    for doc in docs:
        employee = doc.to_dict()
        employee['id'] = doc.id
        employees.append(employee)
    return employees

def get_employee(employee_id):
    """Get single employee by ID"""
    doc = db.collection('employees').document(employee_id).get()
    if doc.exists:
        employee = doc.to_dict()
        employee['id'] = doc.id
        return employee
    return None

# === PAYROLL RUNS ===

def create_payroll_run(month, issued_date, selected_employee_ids):
    """Create a new payroll run with lines for selected employees"""
    # Create the payroll run document
    run_ref = db.collection('payroll_runs').document()
    run_data = {
        'month': month,
        'issued_date': issued_date,
        'created_at': datetime.now()
    }
    run_ref.set(run_data)
    
    # Create payroll lines for each selected employee
    for emp_id in selected_employee_ids:
        employee = get_employee(emp_id)
        if employee:
            # Calculate statutory deductions total
            statutory_total = (
                employee.get('epf_deduction', 0) +
                employee.get('socso_deduction', 0) +
                employee.get('eis_deduction', 0) +
                employee.get('zakat_deduction', 0) +
                employee.get('pcb_deduction', 0) +
                employee.get('hrdf_deduction', 0)
            )
            
            salary = employee.get('base_salary', 0)
            
            line_ref = run_ref.collection('lines').document()
            line_data = {
                'payroll_run_id': run_ref.id,
                'employee_ref': emp_id,
                'name': employee.get('name'),
                'email': employee.get('email'),
                'role': employee.get('role'),
                'nationality': employee.get('nationality'),
                'employee_id': employee.get('employee_id'),
                'passport': employee.get('passport'),
                'epf_no': employee.get('epf_no'),
                'socso_no': employee.get('socso_no'),
                'gender': employee.get('gender'),
                'salary': salary,
                # Statutory deductions snapshot
                'epf_deduction': employee.get('epf_deduction', 0),
                'socso_deduction': employee.get('socso_deduction', 0),
                'eis_deduction': employee.get('eis_deduction', 0),
                'zakat_deduction': employee.get('zakat_deduction', 0),
                'pcb_deduction': employee.get('pcb_deduction', 0),
                'hrdf_deduction': employee.get('hrdf_deduction', 0),
                'statutory_deductions_total': statutory_total,
                # Employer contributions snapshot
                'employer_epf': employee.get('employer_epf', 0),
                'employer_socso': employee.get('employer_socso', 0),
                'employer_eis': employee.get('employer_eis', 0),
                'employer_zakat': employee.get('employer_zakat', 0),
                'employer_pcb': employee.get('employer_pcb', 0),
                'employer_hrdf': employee.get('employer_hrdf', 0),
                'adhoc_deductions_total': 0,
                'total_deductions': statutory_total,  # Initially just statutory
                'net_pay': salary - statutory_total,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            line_ref.set(line_data)
    
    return run_ref.id

def get_payroll_run(run_id):
    """Get payroll run by ID"""
    doc = db.collection('payroll_runs').document(run_id).get()
    if doc.exists:
        run = doc.to_dict()
        run['id'] = doc.id
        return run
    return None

def get_payroll_lines(run_id):
    """Get all payroll lines for a run"""
    lines = []
    docs = db.collection('payroll_runs').document(run_id).collection('lines').stream()
    for doc in docs:
        line = doc.to_dict()
        line['id'] = doc.id
        lines.append(line)
    return lines

def get_all_payroll_runs():
    """Get all payroll runs, ordered by creation date (newest first)"""
    runs = []
    docs = db.collection('payroll_runs').order_by('created_at', direction='DESCENDING').stream()
    
    for doc in docs:
        run = doc.to_dict()
        run['id'] = doc.id
        
        # Count how many employees in this run
        lines_count = len(list(doc.reference.collection('lines').stream()))
        run['employee_count'] = lines_count
        
        runs.append(run)
    
    return runs