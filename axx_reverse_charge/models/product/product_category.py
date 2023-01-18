from odoo import api, fields, models, _


class AxxProductCategory(models.Model):
    _inherit = 'product.category'

    axx_is_rc_relevant = fields.Boolean(string='Is RC Relevant', default=False)
    axx_is_additional_service = fields.Boolean(string='Is Additional Service', default=False)
