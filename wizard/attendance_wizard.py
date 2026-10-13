# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

STATUS = [
    ('present', 'Present'),
    ('absent', 'Absent'),
    ('late', 'Late'),
    ('excused', 'Excused'),
]


class AttendanceWizard(models.TransientModel):
    _name = 'school.attendance.wizard'
    _description = 'Take Class Attendance'

    class_id = fields.Many2one('school.class', string='Class', required=True, readonly=True)
    class_course_ids = fields.Many2many(related='class_id.course_ids')
    course_id = fields.Many2one('school.course', string='Course (optional)',
                                domain="[('id', 'in', class_course_ids)]")
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    line_ids = fields.One2many('school.attendance.wizard.line', 'wizard_id', string='Students')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        class_id = res.get('class_id') or self.env.context.get('default_class_id')
        if class_id and 'line_ids' in fields_list:
            students = self.env['school.class'].browse(class_id).student_ids
            res['line_ids'] = [(0, 0, {'student_id': s.id, 'status': 'present'}) for s in students]
        return res

    def action_mark_all(self):
        """Set every line to the status given in the context (used by the quick buttons)."""
        status = self.env.context.get('mark_status')
        if status:
            self.line_ids.write({'status': status})
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_create_attendance(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("This class has no students. Add students to the class first."))
        Attendance = self.env['school.attendance']
        created = Attendance
        skipped = 0
        not_enrolled = 0
        allowed = self.class_id.student_ids
        if self.course_id and self.course_id.student_ids:
            allowed = allowed & self.course_id.student_ids
        for line in self.line_ids:
            if line.student_id not in allowed:
                not_enrolled += 1
                continue
            exists = Attendance.search_count([
                ('student_id', '=', line.student_id.id),
                ('class_id', '=', self.class_id.id),
                ('course_id', '=', self.course_id.id or False),
                ('date', '=', self.date),
            ])
            if exists:
                skipped += 1
                continue
            vals = {
                'class_id': self.class_id.id,
                'course_id': self.course_id.id or False,
                'student_id': line.student_id.id,
                'date': self.date,
                'status': line.status,
                'remarks': line.remarks,
            }
            if line.status in ('present', 'late'):
                vals['check_in_time'] = fields.Datetime.now()
            created |= Attendance.create(vals)
        self.class_id.message_post(body=_(
            "Attendance taken for %(date)s: %(created)s created, %(skipped)s already existed, "
            "%(not_enrolled)s not enrolled in the course.",
            date=self.date, created=len(created), skipped=skipped, not_enrolled=not_enrolled))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Attendance'),
            'res_model': 'school.attendance',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', created.ids)],
        }


class AttendanceWizardLine(models.TransientModel):
    _name = 'school.attendance.wizard.line'
    _description = 'Take Class Attendance Line'

    wizard_id = fields.Many2one('school.attendance.wizard', required=True, ondelete='cascade')
    student_id = fields.Many2one('res.partner', string='Student', required=True)
    status = fields.Selection(STATUS, string='Status', required=True, default='present')
    remarks = fields.Char(string='Remarks')
