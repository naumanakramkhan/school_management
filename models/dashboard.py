# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SchoolDashboard(models.Model):
    _name = 'school.dashboard'
    _description = 'School Dashboard'

    name = fields.Char(string='Dashboard', default='School Dashboard')

    # Student Statistics
    total_students = fields.Integer(string='Total Students', compute='_compute_statistics')
    male_students = fields.Integer(string='Male Students', compute='_compute_statistics')
    female_students = fields.Integer(string='Female Students', compute='_compute_statistics')

    # Teacher Statistics
    total_teachers = fields.Integer(string='Total Teachers', compute='_compute_statistics')

    # Class Statistics
    total_classes = fields.Integer(string='Total Classes', compute='_compute_statistics')
    active_classes = fields.Integer(string='Active Classes', compute='_compute_statistics')

    # Attendance Statistics
    total_attendance_records = fields.Integer(string='Total Attendance Records', compute='_compute_statistics')
    present_today = fields.Integer(string='Present Today', compute='_compute_statistics')
    absent_today = fields.Integer(string='Absent Today', compute='_compute_statistics')
    attendance_rate = fields.Float(string='Attendance Rate (%)', compute='_compute_statistics')

    # Finance / Fee Statistics
    total_fee_submitted = fields.Float(string='Total Fee Submitted', compute='_compute_statistics')

    @api.depends('name')
    def _compute_statistics(self):
        for record in self:
            # Student statistics
            students = self.env['res.partner'].search([('is_student', '=', True)])
            record.total_students = len(students)
            record.male_students = len(students.filtered(lambda s: s.student_gender == 'male'))
            record.female_students = len(students.filtered(lambda s: s.student_gender == 'female'))

            # Teacher statistics
            record.total_teachers = self.env['res.partner'].search_count([('is_teacher', '=', True)])

            # Class statistics
            if 'school.class' in self.env:
                classes = self.env['school.class'].search([])
                record.total_classes = len(classes)
                record.active_classes = len(classes.filtered(lambda c: getattr(c, 'active', True)))
            else:
                record.total_classes = 0
                record.active_classes = 0

            # Attendance statistics
            if 'school.attendance' in self.env:
                all_attendance = self.env['school.attendance'].search([])
                record.total_attendance_records = len(all_attendance)

                today = fields.Date.context_today(self)
                today_attendance = all_attendance.filtered(lambda a: a.date == today)
                record.present_today = len(today_attendance.filtered(lambda a: a.status == 'present'))
                record.absent_today = len(today_attendance.filtered(lambda a: a.status == 'absent'))

                if len(today_attendance) > 0:
                    record.attendance_rate = (record.present_today / len(today_attendance)) * 100
                else:
                    record.attendance_rate = 0.0
            else:
                record.total_attendance_records = 0
                record.present_today = 0
                record.absent_today = 0
                record.attendance_rate = 0.0

            # Fee statistics calculation options:
            if 'school.fee' in self.env:
                # Dynamic mode: if a fee model exists
                paid_fees = self.env['school.fee'].search([('state', '=', 'paid')])
                record.total_fee_submitted = sum(paid_fees.mapped('amount'))
            elif hasattr(self.env['res.partner'], 'fee_submitted'):
                # Student record flag mode: count students with fee_submitted == True
                paid_students = self.env['res.partner'].search_count(
                    [('is_student', '=', True), ('fee_submitted', '=', True)])
                record.total_fee_submitted = float(paid_students)
            else:
                # Manual hardcoded value for testing/demo purposes
                record.total_fee_submitted = 2.0  # Or set total amount e.g. 10000.00