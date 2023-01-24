from odoo import api, fields, models, _


class AxxSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def onchange_rc_related(self):
        for line in self:
            if line.product_id:
                line.axx_is_rc_relevant = line.product_id.categ_id.axx_is_rc_relevant
                line.axx_is_additional_service = line.product_id.categ_id.axx_is_additional_service

    axx_is_rc_relevant = fields.Boolean(string='Is RC Relevant', default=False)
    axx_is_additional_service = fields.Boolean(string='Is Additional Service', default=False)
    axx_is_rc_calculation_done = fields.Boolean(string='Is RC calculated', default=False)

    @api.depends('product_id')
    def _compute_tax_id(self):
        for line in self:
            rc_relevant_total = sum(line.order_id.order_line.filtered(
                    lambda line_id: line_id.axx_is_rc_relevant and
                                    not line_id.axx_is_additional_service).mapped('price_subtotal'))
            if line.axx_is_rc_relevant and rc_relevant_total > 5000:
                tax_id = self.env['account.tax'].search(
                    [('name', '=ilike', '0% Umsatzsteuer Lieferung von Mobilfunkgeräten u.a. (§13b)'),
                     ('type_tax_use', '=', 'sale'), ('company_id', '=', line.company_id.id)], limit=1)
                line.tax_id = tax_id
            elif line.axx_is_rc_relevant and rc_relevant_total <= 5000:
                super(AxxSaleOrderLine, self)._compute_tax_id()
            else:
                super(AxxSaleOrderLine, self)._compute_tax_id()

    @api.onchange('product_uom_qty', 'price_unit')
    def axx_onchange_subtotal(self):
        for line in self:
            rc_relevant_total = sum(line.order_id.order_line.filtered(
                lambda line_id: line_id.axx_is_rc_relevant and
                                not line_id.axx_is_additional_service).mapped('price_subtotal'))
            if line.axx_is_rc_relevant and rc_relevant_total > 5000:
                tax_id = self.env['account.tax'].search(
                    [('name', '=ilike', '0% Umsatzsteuer Lieferung von Mobilfunkgeräten u.a. (§13b)'),
                     ('type_tax_use', '=', 'sale'), ('company_id', '=', line.company_id.id)], limit=1)
                line.tax_id = tax_id
            elif line.axx_is_rc_relevant and rc_relevant_total <= 5000:
                line._compute_tax_id()
            else:
                line._compute_tax_id()

    def _prepare_invoice_line(self, **optional_values):
        """
        To get the rc related income account from the category
        """
        invoice_line = super()._prepare_invoice_line(**optional_values)
        rc_relevant_total = sum(self.order_id.order_line.filtered(
            lambda line_id: line_id.axx_is_rc_relevant and
                            not line_id.axx_is_additional_service).mapped('price_subtotal'))
        if rc_relevant_total > 5000 and self.axx_is_rc_relevant:
            invoice_line['account_id'] = self.product_template_id.categ_id.axx_rc_income_acc_id and \
                                         self.product_template_id.categ_id.axx_rc_income_acc_id.id or \
                                         self.product_template_id.categ_id.property_account_income_categ_id.id
        return invoice_line
