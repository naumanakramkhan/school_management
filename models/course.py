# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Course(models.Model):
    _name = 'school.course'
    _description = 'Course'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Course Name', required=True, tracking=True)
    course_code = fields.Char(string='Course Code', required=True, copy=False, readonly=True,
                              default='New', tracking=True)
    description = fields.Text(string='Description')
    
    # Many2one: One course belongs to one teacher
    teacher_id = fields.Many2one('res.partner', string='Teacher', tracking=True,
                                 domain=[('is_teacher', '=', True)])
    
    # Many2many: One course can have many students
    student_ids = fields.Many2many('res.partner', 'school_course_school_student_rel',
                                  'school_course_id', 'school_student_id',
                                  string='Students', domain=[('is_student', '=', True)])
    
    # Computed field: count of enrolled students
    student_count = fields.Integer(string='Student Count', compute='_compute_student_count', store=True)
    
    class_ids = fields.Many2many('school.class', 'school_class_course_rel', 'course_id', 'class_id',
                                 string='Classes')
    credits = fields.Integer(string='Credits')
    duration_hours = fields.Float(string='Duration (Hours)')
    start_date = fields.Date(string='Start Date', tracking=True)
    end_date = fields.Date(string='End Date', tracking=True)
    active = fields.Boolean(string='Active', default=True)
    
    @api.depends('student_ids')
    def _compute_student_count(self):
        for record in self:
            record.student_count = len(record.student_ids)
    
    # Auto-generate Course Code on creation
    @api.model
    def create(self, vals):
        if vals.get('course_code', 'New') == 'New':
            vals['course_code'] = self.env['ir.sequence'].next_by_code('school.course') or 'New'
        return super(Course, self).create(vals)
    
    _sql_constraints = [
        ('course_code_unique', 'unique(course_code)', 'Course Code must be unique!')
    ]
