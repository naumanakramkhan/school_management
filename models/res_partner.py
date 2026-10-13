# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    """Students and teachers are regular Contacts flagged with is_student / is_teacher."""
    _inherit = 'res.partner'

    # Students
    is_student = fields.Boolean(string='Is a Student', default=False)
    student_code = fields.Char(string='Student ID', copy=False, readonly=True, index=True)
    student_dob = fields.Date(string='Date of Birth')
    student_age = fields.Integer(string='Age', compute='_compute_student_age')
    student_gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], string='Gender')

    # Teachers
    is_teacher = fields.Boolean(string='Is a Teacher', default=False)
    teacher_code = fields.Char(string='Teacher ID', copy=False, readonly=True, index=True)
    teacher_subject = fields.Char(string='Subject')
    teacher_qualification = fields.Char(string='Qualification')
    teacher_joining_date = fields.Date(string='Date of Joining')
    teacher_experience_years = fields.Integer(string='Years of Experience')

    # Multiple Classes & Courses (Many2many)
    student_class_ids = fields.Many2many(
        'school.class', 'school_class_student_rel', 'student_id', 'class_id',
        string='Classes Enrolled')
    teacher_class_ids = fields.Many2many(
        'school.class', 'school_class_teacher_rel', 'teacher_id', 'class_id',
        string='Teacher Classes')
    student_course_ids = fields.Many2many(
        'school.course', 'school_course_school_student_rel', 'school_student_id', 'school_course_id',
        string='Courses Enrolled')
    teacher_course_ids = fields.Many2many(
        'school.course', string='Courses Taught',
        compute='_compute_teacher_course_ids', inverse='_inverse_teacher_course_ids')

    _sql_constraints = [
        ('student_code_unique', 'unique(student_code)', 'Student ID must be unique!'),
        ('teacher_code_unique', 'unique(teacher_code)', 'Teacher ID must be unique!'),
    ]

    @api.depends('student_dob')
    def _compute_student_age(self):
        today = fields.Date.context_today(self)
        for rec in self:
            dob = rec.student_dob
            if dob:
                rec.student_age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            else:
                rec.student_age = 0

    def _compute_teacher_course_ids(self):
        Course = self.env['school.course']
        for rec in self:
            origin_id = rec._origin.id
            rec.teacher_course_ids = Course.search([('teacher_id', '=', origin_id)]) if origin_id else Course.browse()

    def _inverse_teacher_course_ids(self):
        Course = self.env['school.course']
        for rec in self:
            current = Course.search([('teacher_id', '=', rec.id)])
            (current - rec.teacher_course_ids).write({'teacher_id': False})
            (rec.teacher_course_ids - current).write({'teacher_id': rec.id})

    def _assign_school_codes(self):
        Seq = self.env['ir.sequence']
        for rec in self.filtered(lambda r: r.is_student and not r.student_code):
            rec.student_code = Seq.next_by_code('school.student')
        for rec in self.filtered(lambda r: r.is_teacher and not r.teacher_code):
            rec.teacher_code = Seq.next_by_code('school.teacher')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._assign_school_codes()
        return records

    def write(self, vals):
        res = super().write(vals)
        if vals.get('is_student') or vals.get('is_teacher'):
            self._assign_school_codes()
        return res