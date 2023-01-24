from odoo import api, fields, models, _


class AxxProductCategory(models.Model):
    _inherit = 'product.category'

    axx_is_rc_relevant = fields.Boolean(string='Is RC Relevant', default=False)
    axx_is_additional_service = fields.Boolean(string='Is Additional Service', default=False)
    axx_rc_income_acc_id = fields.Many2one(comodel_name='account.account', string='RC Income Account')
    axx_rc_expense_acc_id = fields.Many2one(comodel_name='account.account', string='RC Expense Account')
