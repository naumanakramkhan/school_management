# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SchoolClass(models.Model):
    """A class / section of students, e.g. "Grade 5 - A"."""
    _name = 'school.class'
    _description = 'School Class'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char(string='Class Name', required=True, tracking=True)
    code = fields.Char(string='Code')
    color = fields.Integer(string='Color Index', default=0)  # <-- Added color field for Kanban / M2M tag widgets
    academic_year = fields.Char(string='Academic Year', help="e.g. 2026-2027")

    class_teacher_id = fields.Many2one('res.partner', string='Class Teacher', tracking=True,
                                       domain=[('is_teacher', '=', True)])
    teacher_ids = fields.Many2many('res.partner', 'school_class_teacher_rel',
                                   'class_id', 'teacher_id', string='Teachers',
                                   domain=[('is_teacher', '=', True)])
    student_ids = fields.Many2many('res.partner', 'school_class_student_rel',
                                   'class_id', 'student_id', string='Students',
                                   domain=[('is_student', '=', True)])
    course_ids = fields.Many2many('school.course', 'school_class_course_rel',
                                  'class_id', 'course_id', string='Courses')
    student_count = fields.Integer(string='Students', compute='_compute_student_count', store=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Class code must be unique!'),
    ]

    @api.depends('student_ids')
    def _compute_student_count(self):
        for rec in self:
            rec.student_count = len(rec.student_ids)

    def action_take_attendance(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Take Attendance'),
            'res_model': 'school.attendance.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_class_id': self.id},
        }