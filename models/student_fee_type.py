# -*- coding: utf-8 -*-

from odoo import models, fields


class StudentFeeType(models.Model):
    """A kind of fee (tuition, admission, exam...). The linked service product
    decides which income account the invoice line is posted to."""
    _name = 'student.fee.type'
    _description = 'Student Fee Type'
    _order = 'sequence, name'

    name = fields.Char(string='Fee Type', required=True, translate=True)
    code = fields.Char(string='Code')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    product_id = fields.Many2one(
        'product.product', string='Product', required=True,
        domain=[('detailed_type', '=', 'service'), ('sale_ok', '=', True)],
        help="Service product used on the invoice line. Its Income Account "
             "(Accounting tab) decides where the fee is posted in the ledger.")
    account_id = fields.Many2one(
        'account.account', string='Income Account Override',
        domain=[('account_type', 'in', ('income', 'income_other')), ('deprecated', '=', False)],
        help="Optional. Leave empty to use the product's income account.")
    default_amount = fields.Float(string='Default Amount')
    description = fields.Text(string='Description')

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Fee type code must be unique!'),
    ]
