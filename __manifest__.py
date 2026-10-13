# -*- coding: utf-8 -*-
{
    'name': 'Future Scholars Academy',
    'version': '17.0.1.8.0',
    'category': 'Education',
    'summary': 'Manage students, teachers, courses, attendance, grades and fee invoicing',
    'description': """
School Management System
========================
This module helps you manage:
- Students
- Teachers
- Courses/Classes
- Attendance tracking
- Grades management
- Student Fee Invoicing & Accounting Integration
- Dashboard and reports
    """,
    'author': 'Your Name',
    'website': 'https://www.yourwebsite.com',
    'depends': ['base', 'mail', 'account'],
    'data': [
        'security/ir.model.access.csv',
        #'data/sequence.xml',
        'data/fee_type_data.xml',
        'data/dashboard_data.xml',
       # 'data/demo_data.xml',
        'views/fee_receipt_template.xml',  # Corrected path to views folder
        'report/fee_receipt_action.xml',   # Added report action
        'views/student_views.xml',
        'views/teacher_views.xml',
        'views/course_views.xml',
        'views/class_views.xml',
        'views/attendance_views.xml',
        'views/attendance_wizard_views.xml',
        'views/grade_views.xml',
        'views/finance_views.xml',
        'views/dashboard_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}