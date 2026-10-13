# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Student(models.Model):
    _name = 'school.student'
    _description = 'Student'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Student Name', required=True, tracking=True)
    student_id = fields.Char(string='Student ID', required=True, copy=False, readonly=True, 
                             default='New', tracking=True)
    age = fields.Integer(string='Age', tracking=True)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string='Gender', tracking=True)
    email = fields.Char(string='Email', tracking=True)
    phone = fields.Char(string='Phone', tracking=True)
    date_of_birth = fields.Date(string='Date of Birth', tracking=True)
    address = fields.Text(string='Address')
    active = fields.Boolean(string='Active', default=True)
    
    # Compute field for age based on date of birth
    @api.depends('date_of_birth')
    def _compute_age(self):
        for record in self:
            if record.date_of_birth:
                today = fields.Date.today()
                record.age = today.year - record.date_of_birth.year
            else:
                record.age = 0
    
    # Auto-generate Student ID on creation
    @api.model
    def create(self, vals):
        if vals.get('student_id', 'New') == 'New':
            vals['student_id'] = self.env['ir.sequence'].next_by_code('school.student') or 'New'
        return super(Student, self).create(vals)
    
    _sql_constraints = [
        ('student_id_unique', 'unique(student_id)', 'Student ID must be unique!')
    ]
