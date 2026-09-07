{
    'name': "KI Payroll Report",
    'summary': "KI Payroll Report",
    'description': """ 
            This Module Print  Payroll Report.
     """,
    'author': "Kiran Infosoft",
    'website': "www.kiraninfosoft.com",
    'category': 'Payroll',
    'version': '0.2',
    'depends': ['hr', 'hr_payroll', 'ph_payroll_computation'],
    'data': [
        # 'data/payroll_register_excel_report.xml',
        'views/hr_payslip_run_inherit.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1,
}
