# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class StudentFee(models.Model):
    _name = 'student.fee'
    _description = 'Student Fee Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Fee Reference', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    student_id = fields.Many2one('res.partner', string='Student', required=True, tracking=True,
                                 domain=[('is_student', '=', True)])
    fee_type_id = fields.Many2one('student.fee.type', string='Fee Type', required=True, tracking=True)
    amount = fields.Monetary(string='Fee Amount', required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    date = fields.Date(string='Fee Date', default=fields.Date.context_today, required=True)
    due_date = fields.Date(string='Due Date')
    note = fields.Text(string='Notes')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('invoiced', 'Invoiced'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    # Link to Odoo's built-in Customer Invoice (this is what posts to the ledgers)
    move_id = fields.Many2one('account.move', string='Customer Invoice', readonly=True, copy=False)
    payment_state = fields.Selection(related='move_id.payment_state', string='Payment Status',
                                     store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('student.fee') or _('New')
        return super().create(vals_list)

    @api.onchange('fee_type_id')
    def _onchange_fee_type_id(self):
        if self.fee_type_id and self.fee_type_id.default_amount:
            self.amount = self.fee_type_id.default_amount

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_("The fee amount must be greater than zero."))

    def unlink(self):
        if any(rec.state == 'invoiced' for rec in self):
            raise UserError(_("You cannot delete an invoiced fee. Cancel it first."))
        return super().unlink()

    def _prepare_invoice_vals(self):
        self.ensure_one()
        fee_type = self.fee_type_id
        line = {
            'product_id': fee_type.product_id.id,
            'name': "%s - %s (%s)" % (fee_type.name, self.student_id.name, self.name),
            'quantity': 1,
            'price_unit': self.amount,
        }
        if fee_type.account_id:
            line['account_id'] = fee_type.account_id.id
        vals = {
            'move_type': 'out_invoice',
            'partner_id': self.student_id.id,
            'invoice_date': self.date,
            'ref': self.name,
            'invoice_origin': self.name,
            'currency_id': self.currency_id.id,
            'company_id': self.company_id.id,
            'invoice_line_ids': [(0, 0, line)],
        }
        if self.due_date:
            vals['invoice_date_due'] = self.due_date
        return vals

    def action_create_invoice(self):
        """Create and POST a customer invoice so it lands in the accounting ledgers."""
        for rec in self:
            if rec.move_id:
                raise UserError(_("An invoice has already been created for this fee record."))
            invoice = self.env['account.move'].with_company(rec.company_id).create(rec._prepare_invoice_vals())
            invoice.action_post()
            rec.write({'move_id': invoice.id, 'state': 'invoiced'})
        return True

    def action_view_invoice(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Customer Invoice'),
            'res_model': 'account.move',
            'res_id': self.move_id.id,
            'view_mode': 'form',
        }

    def action_cancel(self):
        for rec in self:
            move = rec.move_id
            if move:
                if move.payment_state in ('paid', 'in_payment', 'partial', 'reversed'):
                    raise UserError(_("This invoice already has payments. Unreconcile or "
                                      "refund it in Accounting before cancelling the fee."))
                if move.state == 'posted':
                    move.button_draft()
                if move.state == 'draft':
                    move.button_cancel()
            rec.state = 'cancel'
        return True

    def action_reset_draft(self):
        for rec in self:
            if rec.move_id and rec.move_id.state != 'cancel':
                raise UserError(_("The linked invoice is not cancelled."))
            rec.write({'move_id': False, 'state': 'draft'})
        return True
