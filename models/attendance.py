# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Attendance(models.Model):
    _name = 'school.attendance'
    _description = 'Student Attendance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'student_id'
    _order = 'date desc, id desc'

    # Attendance can be taken for a class, for a course, or for both
    class_id = fields.Many2one('school.class', string='Class', tracking=True)
    course_id = fields.Many2one('school.course', string='Course', tracking=True)

    # Updated student_id domain: Allows picking any active student by default
    student_id = fields.Many2one(
        'res.partner',
        string='Student',
        required=True,
        tracking=True,
        domain="[('is_student', '=', True)]"
    )

    date = fields.Date(string='Date', required=True, default=fields.Date.today, tracking=True)

    status = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused')
    ], string='Status', required=True, default='present', tracking=True)

    remarks = fields.Text(string='Remarks')
    check_in_time = fields.Datetime(string='Check-in Time')
    check_out_time = fields.Datetime(string='Check-out Time')

    # Related fields
    student_name = fields.Char(related='student_id.name', string='Student Name', store=True)
    class_name = fields.Char(related='class_id.name', string='Class Name', store=True)
    course_name = fields.Char(related='course_id.name', string='Course Name', store=True)

    def _get_allowed_students(self):
        """Returns relevant students for selected class and/or course."""
        self.ensure_one()
        all_students = self.env['res.partner'].search([('is_student', '=', True)])

        if self.class_id and self.course_id:
            students_in_course = self.env['res.partner'].search([
                ('is_student', '=', True),
                ('student_course_ids', 'in', self.course_id.id)
            ])
            return self.class_id.student_ids & students_in_course
        elif self.class_id:
            return self.class_id.student_ids
        elif self.course_id:
            return self.env['res.partner'].search([
                ('is_student', '=', True),
                ('student_course_ids', 'in', self.course_id.id)
            ])

        return all_students

    @api.onchange('class_id', 'course_id')
    def _onchange_class_course(self):
        """Dynamically filters the student dropdown list when class or course changes."""
        allowed_students = self._get_allowed_students()

        # Reset student selection if current student is not in the filtered list
        if self.student_id and self.student_id not in allowed_students:
            self.student_id = False

        # Return domain to dynamically filter dropdown in UI
        return {
            'domain': {
                'student_id': [('id', 'in', allowed_students.ids)]
            }
        }

    @api.constrains('student_id', 'class_id', 'course_id')
    def _check_student_relevant(self):
        if self.env.context.get('install_mode'):
            return
        for rec in self:
            if rec.class_id or rec.course_id:
                allowed = rec._get_allowed_students()
                if rec.student_id not in allowed:
                    raise ValidationError(_(
                        "%s is not enrolled in the selected class or course.", rec.student_id.display_name))

    @api.constrains('class_id', 'course_id')
    def _check_class_or_course(self):
        for rec in self:
            if not rec.class_id and not rec.course_id:
                raise ValidationError(_("Please select a class or a course for this attendance record."))

    @api.constrains('student_id', 'class_id', 'course_id', 'date')
    def _check_unique_attendance(self):
        for rec in self:
            duplicate = self.search_count([
                ('id', '!=', rec.id),
                ('student_id', '=', rec.student_id.id),
                ('class_id', '=', rec.class_id.id or False),
                ('course_id', '=', rec.course_id.id or False),
                ('date', '=', rec.date),
            ])
            if duplicate:
                raise ValidationError(_("Attendance record already exists for this student, class/course, and date!"))

    @api.onchange('status')
    def _onchange_status(self):
        if self.status in ['present', 'late'] and not self.check_in_time:
            self.check_in_time = fields.Datetime.now()