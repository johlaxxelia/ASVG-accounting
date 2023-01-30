from odoo import api, fields, models, _


class AxxProductTemplate(models.Model):
    _inherit = 'product.template'

    def _get_product_accounts(self):
        res = super(AxxProductTemplate, self)._get_product_accounts()
        if self.env.context.get('rc_stock_valuation', False):
            res.update({
                'stock_valuation': self.categ_id.axx_rc_stock_valuation_acc_id or
                                   self.categ_id.property_stock_valuation_account_id or False,
            })
        return res
