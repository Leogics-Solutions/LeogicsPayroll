from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from io import BytesIO
from datetime import datetime
from reportlab.platypus import Image
import os
from django.conf import settings

COMPANY_NAME = "Leogics Solutions (M) Sdn. Bhd."
COMPANY_ADDRESS = "06-01 & 06M-01, Level 6 & 6M, Menara EcoWorld, Bukit Bintang City Centre, 2, Jln Hang Tuah, Pudu<br/>55100, Wilayah Persekutuan Kuala Lumpur"
COMPANY_REGISTRATION = "Business registration number: 202501000353 (1601768-D)"

def format_month_year(month_str):
    """Convert '2025-12' to 'December 2025'"""
    try:
        date_obj = datetime.strptime(month_str, '%Y-%m')
        return date_obj.strftime('%B %Y')
    except:
        return month_str

def generate_payroll_pdf(run, lines):
    """Generate a PDF matching the PayrollPanda layout"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        topMargin=1.5*cm, 
        bottomMargin=1.5*cm,
        leftMargin=1.5*cm,
        rightMargin=1.5*cm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Process each employee on a separate page
    for idx, line in enumerate(lines):
        if idx > 0:
            elements.append(PageBreak())
        
        elements.extend(create_payslip_page(run, line, styles))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

def create_payslip_page(run, line, styles):
    """Create a single payslip page"""
    page_elements = []
    
    # Format month
    formatted_month = format_month_year(run['month'])
    
    # Header section with logo
    # Try multiple possible paths
    logo_path = os.path.join(settings.BASE_DIR, 'payroll', 'static', 'payroll', 'leogics-logo.png')

    # Debug: print the path (temporary - remove after testing)
    print(f"Looking for logo at: {logo_path}")
    print(f"Logo exists: {os.path.exists(logo_path)}")

    # Check if logo exists
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=2*cm, height=2*cm)  # Adjust size as needed

        header_data = [
            [
                logo,
                Paragraph(f"<b>{COMPANY_NAME}</b><br/>{COMPANY_ADDRESS}<br/><font size=8>{COMPANY_REGISTRATION}</font>", 
                        ParagraphStyle('CompanyHeader', parent=styles['Normal'], fontSize=9, leading=12)),
                Paragraph(f"<b>Payslip for {formatted_month}</b><br/><font size=8>Issued on: {run['issued_date']}</font>", 
                        ParagraphStyle('PayslipHeader', parent=styles['Normal'], fontSize=10, alignment=TA_RIGHT, leading=14))
            ]
        ]

        header_table = Table(header_data, colWidths=[2.5*cm, 9*cm, 6.5*cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (0, 0), 0),
            ('RIGHTPADDING', (0, 0), (0, 0), 8),
        ]))
    else:
        print("Logo not found, using fallback")
        # Fallback if logo not found
        header_data = [
            [
                Paragraph(f"<b>{COMPANY_NAME}</b><br/>{COMPANY_ADDRESS}<br/><font size=8>{COMPANY_REGISTRATION}</font>", 
                        ParagraphStyle('CompanyHeader', parent=styles['Normal'], fontSize=9, leading=12)),
                Paragraph(f"<b>Payslip for {formatted_month}</b><br/><font size=8>Issued on: {run['issued_date']}</font>", 
                        ParagraphStyle('PayslipHeader', parent=styles['Normal'], fontSize=10, alignment=TA_RIGHT, leading=14))
            ]
        ]
        
        header_table = Table(header_data, colWidths=[11*cm, 7*cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))

    page_elements.append(header_table)
    
    # Horizontal line
    line_table = Table([['']], colWidths=[18*cm])
    line_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#333333')),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    page_elements.append(line_table)
    page_elements.append(Spacer(1, 0.3*cm))
    
    # Employee name and title with more spacing
    page_elements.append(Paragraph(f"<b><font size=14>{line['name']}</font></b>", styles['Normal']))
    page_elements.append(Spacer(1, 0.15*cm))  # Added spacing
    page_elements.append(Paragraph(f"<font size=10>{line.get('role', 'N/A')}</font>", styles['Normal']))
    page_elements.append(Spacer(1, 0.3*cm))
    
    # Employee details
    employee_details = [
        [
            Paragraph("<font size=8 color='#666666'>Department</font>", styles['Normal']),
            Paragraph("<font size=8 color='#666666'>Nationality</font>", styles['Normal']),
            Paragraph("<font size=8 color='#666666'>NRIC/Passport</font>", styles['Normal']),
            Paragraph("<font size=8 color='#666666'>EPF No.</font>", styles['Normal'])
        ],
        [
            Paragraph(f"<font size=9>{line.get('department', 'N/A')}</font>", styles['Normal']),
            Paragraph(f"<font size=9>{line.get('nationality', 'N/A')}</font>", styles['Normal']),
            Paragraph(f"<font size=9>{line.get('passport', 'N/A')}</font>", styles['Normal']),
            Paragraph(f"<font size=9>{line.get('epf_no', 'N/A')}</font>", styles['Normal'])
        ],
        [
            Paragraph("<font size=8 color='#666666'>Employee ID</font>", styles['Normal']),
            Paragraph("<font size=8 color='#666666'>Gender</font>", styles['Normal']),
            '',
            Paragraph("<font size=8 color='#666666'>SOCSO No.</font>", styles['Normal'])
        ],
        [
            Paragraph(f"<font size=9>{line.get('employee_id', 'N/A')}</font>", styles['Normal']),
            Paragraph(f"<font size=9>{line.get('gender', 'N/A')}</font>", styles['Normal']),
            '',
            Paragraph(f"<font size=9>{line.get('socso_no', 'N/A')}</font>", styles['Normal'])
        ]
    ]
    
    employee_table = Table(employee_details, colWidths=[4.5*cm, 4.5*cm, 4.5*cm, 4.5*cm])
    employee_table.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    page_elements.append(employee_table)
    
    # Horizontal line
    page_elements.append(Spacer(1, 0.3*cm))
    page_elements.append(line_table)
    page_elements.append(Spacer(1, 0.4*cm))
    
    # Gross Earnings section
    page_elements.append(Paragraph("<b>Gross Earnings</b>", styles['Normal']))
    page_elements.append(Spacer(1, 0.2*cm))
    
    gross_data = [
        [
            Paragraph("<font size=8 color='#666666'>Units</font>", ParagraphStyle('HeaderCenter', alignment=TA_RIGHT, fontSize=8)),
            Paragraph("<font size=8 color='#666666'>Rate</font>", ParagraphStyle('HeaderCenter', alignment=TA_RIGHT, fontSize=8)),
            Paragraph("<font size=8 color='#666666'>Amount</font>", ParagraphStyle('HeaderRight', alignment=TA_RIGHT, fontSize=8))
        ],
        ['', '', ''],
        ['Salary', '', f"{line.get('salary', 0):.2f}"],
        ['', '', ''],
        ['', Paragraph("<b>Gross pay</b>", ParagraphStyle('GrossPay', alignment=TA_RIGHT, fontSize=9)), 
         Paragraph(f"<b>{line.get('salary', 0):.2f}</b>", ParagraphStyle('GrossPayAmount', alignment=TA_RIGHT, fontSize=9))]
    ]
    
    gross_table = Table(gross_data, colWidths=[11*cm, 3.5*cm, 3.5*cm])
    gross_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('BACKGROUND', (2, -1), (2, -1), colors.HexColor('#f5f5f5')),
        ('LEFTPADDING', (2, -1), (2, -1), 10),  # Added left padding for margin
        ('RIGHTPADDING', (2, -1), (2, -1), 10),  # Added right padding for margin
    ]))
    page_elements.append(gross_table)
    
    page_elements.append(Spacer(1, 0.5*cm))
    
    # Contributions section
    page_elements.append(Paragraph("<b>Contributions</b>", styles['Normal']))
    page_elements.append(Spacer(1, 0.2*cm))
    
    # Get employer contributions from stored values
    employer_epf = line.get('employer_epf', 0)
    employer_socso = line.get('employer_socso', 0)
    employer_eis = line.get('employer_eis', 0)
    employer_zakat = line.get('employer_zakat', 0)
    employer_pcb = line.get('employer_pcb', 0)
    employer_hrdf = line.get('employer_hrdf', 0)
    
    # Build contributions table as proper aligned table
    contributions_data = [
        ['', 'EPF', 'SOCSO', 'EIS', 'Zakat', 'PCB', 'HRDF', 'Amount'],
        [
            'Employee',
            f"{line.get('epf_deduction', 0):.2f}",
            f"{line.get('socso_deduction', 0):.2f}",
            f"{line.get('eis_deduction', 0):.2f}",
            f"{line.get('zakat_deduction', 0):.2f}",
            f"{line.get('pcb_deduction', 0):.2f}",
            f"{line.get('hrdf_deduction', 0):.2f}",
            f"-{line.get('statutory_deductions_total', 0):.2f}"
        ],
        [
            'Employer',
            f"{employer_epf:.2f}",
            f"{employer_socso:.2f}",
            f"{employer_eis:.2f}",
            '0.00',
            '0.00',
            '0.00',
            ''
        ]
    ]
    
    contrib_table = Table(contributions_data, colWidths=[3*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2*cm, 3*cm])
    contrib_table.setStyle(TableStyle([
        # Header row
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#666666')),
        ('ALIGN', (1, 0), (-1, 0), 'RIGHT'),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor('#dddddd')),
        
        # Data rows
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        
        # Employer row in gray
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.HexColor('#999999')),
        
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    page_elements.append(contrib_table)
    
    # Ad-hoc deductions if any
    adhoc_deductions = line.get('adhoc_deductions', [])
    if adhoc_deductions:
        page_elements.append(Spacer(1, 0.5*cm))
        page_elements.append(Paragraph("<b>Deductions</b>", styles['Normal']))
        page_elements.append(Spacer(1, 0.2*cm))
        
        adhoc_data = [['', '', 'Amount']]  # Header
        for ded in adhoc_deductions:
            adhoc_data.append([
                ded['name'],
                '',
                f"-{ded['amount']:.2f}"
            ])
        
        adhoc_table = Table(adhoc_data, colWidths=[11*cm, 4*cm, 3*cm])
        adhoc_table.setStyle(TableStyle([
            # Header
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#666666')),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor('#dddddd')),
            
            # Data
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        page_elements.append(adhoc_table)
    
    page_elements.append(Spacer(1, 0.5*cm))
    
    # Net Earnings section
    page_elements.append(Paragraph("<b>Net Earnings</b>", styles['Normal']))
    page_elements.append(Spacer(1, 0.2*cm))
    
    net_data = [
        [
            Paragraph("<font size=8 color='#666666'>Units</font>", ParagraphStyle('HeaderCenter', alignment=TA_RIGHT, fontSize=8)),
            Paragraph("<font size=8 color='#666666'>Rate</font>", ParagraphStyle('HeaderCenter', alignment=TA_RIGHT, fontSize=8)),
            Paragraph("<font size=8 color='#666666'>Amount</font>", ParagraphStyle('HeaderRight', alignment=TA_RIGHT, fontSize=8))
        ],
        ['', '', ''],
        ['', '', ''],
        ['', Paragraph("<b>Net pay</b>", ParagraphStyle('NetPay', alignment=TA_RIGHT, fontSize=9)), 
         Paragraph(f"<b>{line.get('net_pay', 0):.2f}</b>", ParagraphStyle('NetPayAmount', alignment=TA_RIGHT, fontSize=9))],
        ['', '', ''],
        ['', Paragraph("<font size=8 color='#666666'>Taxable pay</font>", ParagraphStyle('TaxablePay', alignment=TA_RIGHT, fontSize=8)), 
         Paragraph(f"<font size=8>{line.get('salary', 0):.2f}</font>", ParagraphStyle('TaxablePayAmount', alignment=TA_RIGHT, fontSize=8))]
    ]
    
    net_table = Table(net_data, colWidths=[11*cm, 3.5*cm, 3.5*cm])
    net_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('BACKGROUND', (2, 3), (2, 3), colors.HexColor('#f5f5f5')),
        ('LEFTPADDING', (2, 3), (2, 3), 10),  # Added left padding for margin
        ('RIGHTPADDING', (2, 3), (2, 3), 10),  # Added right padding for margin
    ]))
    page_elements.append(net_table)
    
    # Footer
    page_elements.append(Spacer(1, 1*cm))
    footer_text = """
    <font size=7 color='#666666'>
    EPF contributions are calculated based on 11.00% employee rate and 13.00% employer rate<br/>
    PCB Calculations are based on the following employee info:<br/>
    Resident, Normal Worker, Single, No Dependent Children<br/>
    <b>Generated from Leogics Payroll System</b>
    </font>
    """
    page_elements.append(Paragraph(footer_text, styles['Normal']))
    
    return page_elements