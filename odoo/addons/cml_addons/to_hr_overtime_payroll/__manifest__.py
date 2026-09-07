{
    'name': "HR Overtime Management",

    'summary': """
        Employee Overtime Management and Payroll Integration""",

    'description': """
This application manages employee overtime (with approval process). It also integrated with Odoo payroll system for automatic calculation in payslips.

Key Features
============

Submit & Approval Process
-------------------------

* Employees can create Overtime Declaration and submit to their Overtime Manager for reviews and approval
* The Manager will get notified when an overtime declaration is submitted.
* Manager can approve/refuse the submitted overtime declaration
* When create payslip, the approved overtime declaration will be calculated and added into the payslip, respecting the rate of each and every Overtime Rule applied

Rules & Master Data
-------------------
1. Rule Code
    * Rule code is a model consist of the following information
        * Code: store a short text present the code for the rules that use this rule code. For example: OT0006, OT0618, etc.
        * Rate: the extra pay in percentage (of basic wage, for example) which can be used in payroll computation.
    * Master Data: once install, the following rule codes will be inserted into your database
        * Codes for overtime in normal working days
            * OT0006
                * Code: OT0006
                * Rate (%): 200
            * OT0618
                * Code: OT0618
                * Rate (%): 150
            * OT1822
                * Code: OT1822
                * Rate (%): 150
            * OT2224
                * Code: OT2224
                * Rate (%): 200
        * Codes for overtime in Saturdays
        * Codes for overtime in Sundays
        * Codes for overtime in holidays
2. Overtime Rule
    * Overtime Rule is a model that allows managers to define rules that will be available for company
    * Each Overtime Rule consists of the following information
        * Name: the name of the rule, for example, Monday Early Morning, Monday Evening, Saturday Evening, etc
        * Day of Week: the day of week that the rule will be applied. For example, Monday, Saturday, etc
        * Hour From & Hour To: the period of time of the day during which the working time will be counted as overtime
        * Rule Code: referring to a rule code for Code and Rate information
        * Company: for usage in multi-company environment
    * Master Data: Upon installation, this application creates most common overtime rules to help you speed up implementation process
        
3. Salary Rule
    Upon installation, this application also creates an additional salary rule for the Base Salary Structure to enable it to calculate overtime pay. The formula is simple and for the sample purpose so that you can modify it to meet your requirements
    
    .. code:: python

      total_hours = sum(line.number_of_hours for line in payslip.worked_days_line_ids)
      hour_cost = total_hours and contract.wage / total_hours or 0.0    
      amount = 0.0
      for line in payslip.payslip_ot_line_ids:
          if payslip.contract_id:
              amount += hour_cost * line.number_of_hours * line.rate / 100
      result = amount

Editions Supported
==================
1. Community Edition
2. Enterprise Edition

    """,

    'author': "T.V.T Marine Automation (aka TVTMA)",
    'website': 'https://www.tvtmarine.com',
    'live_test_url': 'https://v12demo-int.erponline.vn',
    'support': 'support@ma.tvtmarine.com',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '1.0.1',

    # any module necessary for this one to work correctly
    'depends': ['to_hr_payroll_account_advanced', 'hr_holidays', 'to_base', 'to_hr_work_day_type'],

    # always loaded
    'data': [
        'data/module_data.xml',
        'security/hr_overtime_security.xml',
        'security/ir.model.access.csv',
        'data/hr_payroll_data.xml',
        'data/mail_template_data.xml',
        'data/overtime_rule_code.xml',
        'data/overtime_rule.xml',
        'data/overtime_sequence.xml',
        'views/root_menu.xml',
        'views/hr_employee_views.xml',
        'views/hr_overtime_rule_code_views.xml',
        'views/hr_overtime_rule_views.xml',
        'views/hr_overtime_request_single_view.xml',
        'views/hr_contract.xml',
        'views/hr_payslip.xml',
        'views/hr_overtime_line_views.xml',
        'views/hr_overtime_reason_views.xml',

        'views/hr_overtime_request_report.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 99.9,
    'currency': 'EUR',
    'license': 'OPL-1',
}
