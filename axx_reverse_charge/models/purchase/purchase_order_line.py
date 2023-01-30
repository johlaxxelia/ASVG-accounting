from odoo import api, fields, models, _


class AxxPurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    axx_is_rc_relevant = fields.Boolean(string='Is RC Relevant', default=False)
    axx_is_additional_service = fields.Boolean(string='Is Additional Service', default=False)
    axx_is_rc_calculation_done = fields.Boolean(string='Is RC calculated', default=False)

    @api.onchange('product_qty', 'price_unit', 'product_id')
    def axx_onchange_subtotal(self):
        for line in self:
            rc_relevant_total = sum(line.order_id.order_line.filtered(
                lambda line_id: line_id.axx_is_rc_relevant and
                                not line_id.axx_is_additional_service).mapped('price_subtotal'))
            if line.axx_is_rc_relevant and rc_relevant_total > 5000:
                tax_id = self.env['account.tax'].search(
                    [('name', '=ilike', 'Steuer gem. §13b 19%USt/19%VSt (Empfang von Mobilfunkgeräten u.a.)'),
                     ('type_tax_use', '=', 'purchase'), ('company_id', '=', line.company_id.id)], limit=1)
                line.order_id.order_line.filtered('axx_is_rc_relevant').write({'taxes_id': [(6, 0, [tax_id.id])]})
            elif line.axx_is_rc_relevant and rc_relevant_total <= 5000:
                line._compute_tax_id()
            else:
                line._compute_tax_id()

    @api.onchange('product_id')
    def onchange_rc_related(self):
        for line in self:
            if line.product_id:
                line.axx_is_rc_relevant = line.product_id.categ_id.axx_is_rc_relevant
                line.axx_is_additional_service = line.product_id.categ_id.axx_is_additional_service

    def _prepare_account_move_line(self, move=False):
        """
        To get the rc related expense account from the category
        """
        values = super(AxxPurchaseOrderLine, self)._prepare_account_move_line(move)
        rc_relevant_total = sum(self.order_id.order_line.filtered(
            lambda line_id: line_id.axx_is_rc_relevant and
                            not line_id.axx_is_additional_service).mapped('price_subtotal'))
        if rc_relevant_total >= 5000 and self.axx_is_rc_relevant:
            expense_acc_id = self.product_id.categ_id.axx_rc_expense_acc_id and \
                             self.product_id.categ_id.axx_rc_expense_acc_id.id or \
                             self.product_id.property_account_expense_id and \
                             self.product_id.property_account_expense_id.id or \
                             self.product_id.categ_id.property_account_expense_categ_id and \
                             self.product_id.categ_id.property_account_expense_categ_id.id
            # stock_valuation_acc_id = self.categ_id.axx_rc_stock_valuation_acc_id or \
            #                          self.categ_id.property_stock_valuation_account_id or False,
            values.update({
                'account_id': expense_acc_id,
                # 'stock_valuation': stock_valuation_acc_id,
            })
        return values
