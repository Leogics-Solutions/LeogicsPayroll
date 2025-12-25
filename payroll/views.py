from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
import json
import zipfile
from datetime import datetime
from io import BytesIO
from .repository import get_all_employees, create_payroll_run, get_payroll_run, get_payroll_lines
from .pdf_generator import generate_payroll_pdf
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

@login_required
def payroll_list(request):
    """Landing page - will list all payroll runs later"""
    return render(request, 'payroll/payroll_list.html')

@login_required
def payroll_create(request):
    """Create new payroll run"""
    if request.method == 'POST':
        month = request.POST.get('month')
        issued_date = request.POST.get('issued_date')
        selected_employees = request.POST.getlist('employees')
        
        # Create the payroll run
        run_id = create_payroll_run(month, issued_date, selected_employees)
        
        # Redirect to the detail page
        return redirect('payroll_detail', run_id=run_id)
    
    # GET request - show the form
    employees = get_all_employees()
    return render(request, 'payroll/payroll_create.html', {
        'employees': employees
    })

@login_required
def payroll_detail(request, run_id):
    """Payroll detail page - the 'payrolling screen'"""
    run = get_payroll_run(run_id)
    lines = get_payroll_lines(run_id)
    
    return render(request, 'payroll/payroll_detail.html', {
        'run': run,
        'lines': lines
    })

@login_required
@require_http_methods(["GET"])
def get_deductions(request, run_id, line_id):
    """Get payroll line with statutory and ad-hoc deductions"""
    from payroll_mvp.firebase import db
    
    # Get the payroll line
    line_ref = db.collection('payroll_runs').document(run_id).collection('lines').document(line_id)
    line_doc = line_ref.get()
    
    if not line_doc.exists:
        return JsonResponse({'error': 'Line not found'}, status=404)
    
    line_data = line_doc.to_dict()
    line_data['id'] = line_doc.id
    
    # Get ad-hoc deductions
    adhoc_deductions = []
    docs = line_ref.collection('deductions').stream()
    
    for doc in docs:
        deduction = doc.to_dict()
        deduction['id'] = doc.id
        adhoc_deductions.append(deduction)
    
    return JsonResponse({
        'line': line_data,
        'adhoc_deductions': adhoc_deductions
    })

@login_required
@require_http_methods(["POST"])
def save_deductions(request, run_id, line_id):
    """Save ad-hoc deductions for a payroll line"""
    from payroll_mvp.firebase import db
    from datetime import datetime
    
    data = json.loads(request.body)
    adhoc_deductions_data = data.get('adhoc_deductions', [])
    
    # Reference to the line and its deductions subcollection
    line_ref = db.collection('payroll_runs').document(run_id).collection('lines').document(line_id)
    deductions_ref = line_ref.collection('deductions')
    
    # Get current line data
    line_doc = line_ref.get()
    if not line_doc.exists:
        return JsonResponse({'error': 'Line not found'}, status=404)
    
    line_data = line_doc.to_dict()
    
    # Delete all existing ad-hoc deductions
    existing = deductions_ref.stream()
    for doc in existing:
        doc.reference.delete()
    
    # Add new ad-hoc deductions
    adhoc_total = 0
    for idx, ded in enumerate(adhoc_deductions_data):
        if ded['name'] and ded['amount']:
            amount = float(ded['amount'])
            adhoc_total += amount
            
            deductions_ref.add({
                'name': ded['name'],
                'amount': amount,
                'sort_order': idx,
                'created_at': datetime.now()
            })
    
    # Calculate totals
    statutory_total = line_data.get('statutory_deductions_total', 0)
    total_deductions = statutory_total + adhoc_total
    salary = line_data.get('salary', 0)
    net_pay = salary - total_deductions
    
    # Update the payroll line
    line_ref.update({
        'adhoc_deductions_total': adhoc_total,
        'total_deductions': total_deductions,
        'net_pay': net_pay,
        'updated_at': datetime.now()
    })
    
    return JsonResponse({
        'success': True,
        'adhoc_deductions_total': adhoc_total,
        'total_deductions': total_deductions,
        'net_pay': net_pay
    })

@login_required
def download_payroll_pdf(request, run_id):
    """Download combined PDF for entire payroll run"""
    from payroll_mvp.firebase import db
    
    # Get payroll run
    run = get_payroll_run(run_id)
    if not run:
        return HttpResponse('Payroll run not found', status=404)
    
    # Get all lines with their ad-hoc deductions
    lines = []
    line_docs = db.collection('payroll_runs').document(run_id).collection('lines').stream()
    
    for line_doc in line_docs:
        line_data = line_doc.to_dict()
        line_data['id'] = line_doc.id
        
        # Get ad-hoc deductions for this line
        adhoc_deductions = []
        ded_docs = line_doc.reference.collection('deductions').stream()
        for ded_doc in ded_docs:
            ded = ded_doc.to_dict()
            adhoc_deductions.append(ded)
        
        line_data['adhoc_deductions'] = adhoc_deductions
        lines.append(line_data)
    
    # Generate combined PDF
    pdf_buffer = generate_payroll_pdf(run, lines)
    
    # Return as downloadable file
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="payroll_{run["month"]}_combined.pdf"'
    
    return response

@login_required
def download_single_payslip(request, run_id, line_id):
    """Download PDF for a single employee payslip"""
    from payroll_mvp.firebase import db
    
    # Get payroll run
    run = get_payroll_run(run_id)
    if not run:
        return HttpResponse('Payroll run not found', status=404)
    
    # Get the specific payroll line
    line_ref = db.collection('payroll_runs').document(run_id).collection('lines').document(line_id)
    line_doc = line_ref.get()
    
    if not line_doc.exists:
        return HttpResponse('Payroll line not found', status=404)
    
    line_data = line_doc.to_dict()
    line_data['id'] = line_doc.id
    
    # Get ad-hoc deductions
    adhoc_deductions = []
    ded_docs = line_ref.collection('deductions').stream()
    for ded_doc in ded_docs:
        ded = ded_doc.to_dict()
        adhoc_deductions.append(ded)
    
    line_data['adhoc_deductions'] = adhoc_deductions
    
    # Generate PDF for single employee
    pdf_buffer = generate_payroll_pdf(run, [line_data])
    
    # Return as downloadable file
    employee_name = line_data.get('name', 'employee').replace(' ', '_')
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{employee_name}_payslip_{run["month"]}.pdf"'
    
    return response

@login_required
def download_all_payslips_zip(request, run_id):
    """Download all payslips as individual PDFs in a ZIP file"""
    from payroll_mvp.firebase import db
    
    # Get payroll run
    run = get_payroll_run(run_id)
    if not run:
        return HttpResponse('Payroll run not found', status=404)
    
    # Get all lines
    line_docs = db.collection('payroll_runs').document(run_id).collection('lines').stream()
    
    # Create in-memory ZIP file
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for line_doc in line_docs:
            line_data = line_doc.to_dict()
            line_data['id'] = line_doc.id
            
            # Get ad-hoc deductions
            adhoc_deductions = []
            ded_docs = line_doc.reference.collection('deductions').stream()
            for ded_doc in ded_docs:
                ded = ded_doc.to_dict()
                adhoc_deductions.append(ded)
            
            line_data['adhoc_deductions'] = adhoc_deductions
            
            # Generate individual PDF
            pdf_buffer = generate_payroll_pdf(run, [line_data])
            
            # Add to ZIP
            employee_name = line_data.get('name', 'employee').replace(' ', '_')
            filename = f"{employee_name}_payslip_{run['month']}.pdf"
            zip_file.writestr(filename, pdf_buffer.getvalue())
    
    zip_buffer.seek(0)
    
    # Return ZIP file
    month_year = run['month'].replace('-', '_')
    response = HttpResponse(zip_buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="leogics_payslips_{month_year}.zip"'
    
    return response

@login_required
def payroll_list(request):
    """Landing page - list all payroll runs"""
    from .repository import get_all_payroll_runs
    
    runs = get_all_payroll_runs()
    
    return render(request, 'payroll/payroll_list.html', {
        'runs': runs
    }) 

def logout_view(request):
    """Handle logout"""
    logout(request)
    return redirect('login')

@login_required
def employee_list(request):
    """List all employees"""
    employees = get_all_employees()
    
    return render(request, 'payroll/employee_list.html', {
        'employees': employees
    })

@login_required
def employee_create(request):
    """Create a new employee"""
    if request.method == 'POST':
        from payroll_mvp.firebase import db
        
        employee_data = {
            'name': request.POST.get('name'),
            'role': request.POST.get('role'),
            'email': request.POST.get('email'),
            'nationality': request.POST.get('nationality'),
            'employee_id': request.POST.get('employee_id'),
            'passport': request.POST.get('passport'),
            'epf_no': request.POST.get('epf_no'),
            'socso_no': request.POST.get('socso_no'),
            'gender': request.POST.get('gender'),
            'base_salary': float(request.POST.get('base_salary', 0)),
            # Employee deductions
            'epf_deduction': float(request.POST.get('epf_deduction', 0)),
            'socso_deduction': float(request.POST.get('socso_deduction', 0)),
            'eis_deduction': float(request.POST.get('eis_deduction', 0)),
            'zakat_deduction': float(request.POST.get('zakat_deduction', 0)),
            'pcb_deduction': float(request.POST.get('pcb_deduction', 0)),
            'hrdf_deduction': float(request.POST.get('hrdf_deduction', 0)),
            # Employer contributions
            'employer_epf': float(request.POST.get('employer_epf', 0)),
            'employer_socso': float(request.POST.get('employer_socso', 0)),
            'employer_eis': float(request.POST.get('employer_eis', 0)),
            'employer_zakat': float(request.POST.get('employer_zakat', 0)),
            'employer_pcb': float(request.POST.get('employer_pcb', 0)),
            'employer_hrdf': float(request.POST.get('employer_hrdf', 0)),
        }
        
        db.collection('employees').add(employee_data)
        
        return redirect('employee_list')
    
    return render(request, 'payroll/employee_create.html')

@login_required
def employee_edit(request, employee_id):
    """Edit an employee"""
    from payroll_mvp.firebase import db
    from .repository import get_employee
    
    if request.method == 'POST':
        employee_data = {
            'name': request.POST.get('name'),
            'role': request.POST.get('role'),
            'email': request.POST.get('email'),
            'nationality': request.POST.get('nationality'),
            'employee_id': request.POST.get('employee_id'),
            'passport': request.POST.get('passport'),
            'epf_no': request.POST.get('epf_no'),
            'socso_no': request.POST.get('socso_no'),
            'gender': request.POST.get('gender'),
            'base_salary': float(request.POST.get('base_salary', 0)),
            # Employee deductions
            'epf_deduction': float(request.POST.get('epf_deduction', 0)),
            'socso_deduction': float(request.POST.get('socso_deduction', 0)),
            'eis_deduction': float(request.POST.get('eis_deduction', 0)),
            'zakat_deduction': float(request.POST.get('zakat_deduction', 0)),
            'pcb_deduction': float(request.POST.get('pcb_deduction', 0)),
            'hrdf_deduction': float(request.POST.get('hrdf_deduction', 0)),
            # Employer contributions
            'employer_epf': float(request.POST.get('employer_epf', 0)),
            'employer_socso': float(request.POST.get('employer_socso', 0)),
            'employer_eis': float(request.POST.get('employer_eis', 0)),
            'employer_zakat': float(request.POST.get('employer_zakat', 0)),
            'employer_pcb': float(request.POST.get('employer_pcb', 0)),
            'employer_hrdf': float(request.POST.get('employer_hrdf', 0)),
        }
        
        db.collection('employees').document(employee_id).update(employee_data)
        
        return redirect('employee_list')
    
    employee = get_employee(employee_id)
    
    return render(request, 'payroll/employee_edit.html', {
        'employee': employee
    })

@login_required
def employee_delete(request, employee_id):
    """Delete an employee"""
    from payroll_mvp.firebase import db
    
    if request.method == 'POST':
        db.collection('employees').document(employee_id).delete()
        return redirect('employee_list')
    
    from .repository import get_employee
    employee = get_employee(employee_id)
    
    return render(request, 'payroll/employee_delete.html', {
        'employee': employee
    })