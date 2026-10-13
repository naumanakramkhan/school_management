# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Grade(models.Model):
    _name = 'school.grade'
    _description = 'Student Grade'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, student_id'
    
    name = fields.Char(string='Grade Reference', readonly=True, copy=False, default='New')
    student_id = fields.Many2one('res.partner', string='Student', required=True, tracking=True,
                                 ondelete='cascade', domain=[('is_student', '=', True)])
    course_id = fields.Many2one('school.course', string='Course', required=True, tracking=True, ondelete='cascade')
    teacher_id = fields.Many2one(related='course_id.teacher_id', string='Teacher', store=True, readonly=True)
    
    # Grade details
    exam_type = fields.Selection([
        ('quiz', 'Quiz'),
        ('midterm', 'Mid-term Exam'),
        ('final', 'Final Exam'),
        ('assignment', 'Assignment'),
        ('project', 'Project'),
        ('practical', 'Practical Exam')
    ], string='Exam Type', required=True, default='quiz', tracking=True)
    
    date = fields.Date(string='Exam Date', required=True, default=fields.Date.context_today, tracking=True)
    
    # Scoring
    max_score = fields.Float(string='Maximum Score', required=True, default=100.0, tracking=True)
    obtained_score = fields.Float(string='Obtained Score', required=True, tracking=True)
    percentage = fields.Float(string='Percentage (%)', compute='_compute_percentage', store=True)
    
    # Grade calculation
    grade = fields.Selection([
        ('a_plus', 'A+ (90-100%)'),
        ('a', 'A (80-89%)'),
        ('b_plus', 'B+ (75-79%)'),
        ('b', 'B (70-74%)'),
        ('c_plus', 'C+ (65-69%)'),
        ('c', 'C (60-64%)'),
        ('d', 'D (50-59%)'),
        ('f', 'F (Below 50%)')
    ], string='Grade', compute='_compute_grade', store=True)
    
    status = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')
    ], string='Status', compute='_compute_status', store=True)
    
    remarks = fields.Text(string='Remarks', tracking=True)
    
    # SQL constraint
    _sql_constraints = [
        ('unique_student_course_exam', 
         'unique(student_id, course_id, exam_type, date)', 
         'A student can only have one grade per exam type per course per date!')
    ]
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('school.grade.sequence') or 'New'
        return super(Grade, self).create(vals)
    
    @api.depends('obtained_score', 'max_score')
    def _compute_percentage(self):
        for record in self:
            if record.max_score > 0:
                record.percentage = (record.obtained_score / record.max_score) * 100
            else:
                record.percentage = 0.0
    
    @api.depends('percentage')
    def _compute_grade(self):
        for record in self:
            percentage = record.percentage
            if percentage >= 90:
                record.grade = 'a_plus'
            elif percentage >= 80:
                record.grade = 'a'
            elif percentage >= 75:
                record.grade = 'b_plus'
            elif percentage >= 70:
                record.grade = 'b'
            elif percentage >= 65:
                record.grade = 'c_plus'
            elif percentage >= 60:
                record.grade = 'c'
            elif percentage >= 50:
                record.grade = 'd'
            else:
                record.grade = 'f'
    
    @api.depends('percentage')
    def _compute_status(self):
        for record in self:
            record.status = 'pass' if record.percentage >= 50 else 'fail'
    
    @api.constrains('obtained_score', 'max_score')
    def _check_scores(self):
        for record in self:
            if record.max_score <= 0:
                raise ValidationError("Maximum score must be greater than zero!")
            if record.obtained_score < 0:
                raise ValidationError("Obtained score cannot be negative!")
            if record.obtained_score > record.max_score:
                raise ValidationError("Obtained score cannot be greater than maximum score!")
