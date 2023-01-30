from odoo import api, fields, models, _


class StockPickingInherited(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        for picking in self:
            if picking.sale_id:
                order_id = picking.sale_id
            else:
                order_id = self.env['purchase.order'].search([('name', '=ilike', picking.origin)])
            if order_id:
                rc_relevant_total = sum(order_id.order_line.filtered(
                    lambda line_id: line_id.axx_is_rc_relevant and
                                    not line_id.axx_is_additional_service).mapped('price_subtotal'))
                if rc_relevant_total >= 5000:
                    self = self.with_context(rc_stock_valuation=True)
        res = super(StockPickingInherited, self).button_validate()
        return res
