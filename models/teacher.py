# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Teacher(models.Model):
    _name = 'school.teacher'
    _description = 'Teacher'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Teacher Name', required=True, tracking=True)
    teacher_id = fields.Char(string='Teacher ID', required=True, copy=False, readonly=True,
                             default='New', tracking=True)
    subject = fields.Char(string='Subject', tracking=True)
    email = fields.Char(string='Email', tracking=True)
    phone = fields.Char(string='Phone', tracking=True)
    address = fields.Text(string='Address')
    date_of_joining = fields.Date(string='Date of Joining', tracking=True)
    qualification = fields.Char(string='Qualification')
    experience_years = fields.Integer(string='Years of Experience')
    active = fields.Boolean(string='Active', default=True)
    
    # Auto-generate Teacher ID on creation
    @api.model
    def create(self, vals):
        if vals.get('teacher_id', 'New') == 'New':
            vals['teacher_id'] = self.env['ir.sequence'].next_by_code('school.teacher') or 'New'
        return super(Teacher, self).create(vals)
    
    _sql_constraints = [
        ('teacher_id_unique', 'unique(teacher_id)', 'Teacher ID must be unique!')
    ]
