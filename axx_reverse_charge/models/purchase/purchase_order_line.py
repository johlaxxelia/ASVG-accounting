from odoo import api, fields, models, _


class AxxPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    axx_is_active_rc = fields.Boolean(string='Is RC Active', default=True)

    def write(self, vals):
        res = super(AxxPurchaseOrder, self).write(vals)
        for order in self.filtered(lambda po: po.axx_is_active_rc):
            lines_to_delete = []
            price = 0
            for line in order.order_line:
                rc_relevant_total = sum(order.order_line.filtered(
                    lambda line_id: line_id.axx_is_rc_relevant and
                                    not line_id.axx_is_additional_service).mapped('price_subtotal'))
                if line.axx_is_additional_service:
                    if rc_relevant_total > 5000:
                        non_rc_relevant_total = sum(order.order_line.filtered(
                            lambda line_id: not line_id.axx_is_rc_relevant and
                                            not line_id.axx_is_additional_service).mapped('price_subtotal'))
                        if not line.axx_is_rc_calculation_done:
                            if non_rc_relevant_total:
                                additional_service_total = non_rc_relevant_total
                            elif line.axx_is_rc_relevant:
                                additional_service_total = sum(line.order_id.order_line.filtered(
                                    lambda rec: rec.product_id.id == line.product_id.id).mapped('price_unit'))
                            else:
                                additional_service_total = line.price_subtotal
                            if (order.amount_untaxed - additional_service_total) == rc_relevant_total:
                                line.write({'axx_is_rc_relevant': True, 'axx_is_rc_calculation_done': True})
                            else:
                                rc_relevant_perc = (rc_relevant_total / order.amount_untaxed)
                                original_price = line.price_unit
                                line.write({'price_unit': line.price_unit * rc_relevant_perc,
                                            'axx_is_rc_relevant': True, 'axx_is_rc_calculation_done': True})
                                new_line = line.copy(default={'order_id': line.order_id.id,
                                                              'state': line.order_id.state})
                                new_line.write({'price_unit': original_price * (1 - rc_relevant_perc),
                                                'axx_is_rc_relevant': False})
                        else:
                            if non_rc_relevant_total:
                                additional_service_total = non_rc_relevant_total
                            elif line.axx_is_rc_relevant:
                                additional_service_total = sum(line.order_id.order_line.filtered(
                                    lambda rec: rec.product_id.id == line.product_id.id).mapped('price_unit'))
                            else:
                                additional_service_total = line.price_subtotal
                            if (order.amount_untaxed - additional_service_total) == rc_relevant_total:
                                price = sum(line.order_id.order_line.filtered(
                                    lambda rec: rec.product_id.id == line.product_id.id).mapped('price_unit'))
                                line.write({'price_unit': price, 'axx_is_rc_calculation_done': False})
                            elif non_rc_relevant_total:
                                rc_relevant_perc = (rc_relevant_total / order.amount_untaxed)
                                if not price:
                                    price = sum(line.order_id.order_line.filtered(
                                        lambda rec: rec.product_id.id == line.product_id.id).mapped('price_unit'))
                                line.write({'price_unit': price * rc_relevant_perc}) if line.axx_is_rc_relevant else \
                                    line.write({'price_unit': price * (1 - rc_relevant_perc)})
                            else:
                                lines_to_delete.append(line)
                    elif rc_relevant_total <= 5000 and line.axx_is_rc_calculation_done:
                        if line.axx_is_rc_relevant:
                            price = sum(line.order_id.order_line.filtered(
                                lambda rec: rec.product_id.id == line.product_id.id).mapped('price_unit'))
                            line.write({'price_unit': price, 'axx_is_rc_calculation_done': False,
                                        'axx_is_rc_relevant': False})
                        else:
                            lines_to_delete.append(line)
                if line.axx_is_rc_relevant and sum(
                        line.order_id.order_line.filtered(
                            lambda line_id: line_id.axx_is_rc_relevant and
                                            not line_id.axx_is_additional_service).mapped('price_subtotal')) > 5000:
                    tax_id = self.env['account.tax'].search(
                        [('name', '=ilike', 'Steuer gem. §13b 19%USt/19%VSt (Empfang von Mobilfunkgeräten u.a.)'),
                         ('type_tax_use', '=', 'purchase'), ('company_id', '=', line.company_id.id)], limit=1)
                    line.order_id.order_line.filtered('axx_is_rc_relevant').write({'taxes_id': tax_id})
                elif line.axx_is_rc_relevant and sum(
                        line.order_id.order_line.filtered(
                            lambda line_id: line_id.axx_is_rc_relevant and
                                            not line_id.axx_is_additional_service).mapped('price_subtotal')) < 5000:
                    line.order_id.order_line.filtered('axx_is_rc_relevant')._compute_tax_id()
                else:
                    line._compute_tax_id()
            lines_to_delete and [order_line.unlink() for order_line in lines_to_delete]

        for order in self.filtered(lambda po: not po.axx_is_active_rc):
            order.order_line.filtered('axx_is_rc_relevant')._compute_tax_id()

        return res


class AxxPurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    axx_is_rc_relevant = fields.Boolean(string='Is RC Relevant', default=False)
    axx_is_additional_service = fields.Boolean(string='Is Additional Service', default=False)
    axx_is_rc_calculation_done = fields.Boolean(string='Is RC calculated', default=False)

    @api.onchange('product_qty', 'price_unit', 'product_id')
    def axx_onchange_subtotal(self):
        for line in self:
            if line.axx_is_rc_relevant and \
                    sum(line.order_id.order_line.filtered('axx_is_rc_relevant').mapped('price_subtotal')) > 5000:
                tax_id = self.env['account.tax'].search(
                    [('name', '=ilike', 'Steuer gem. §13b 19%USt/19%VSt (Empfang von Mobilfunkgeräten u.a.)'),
                     ('type_tax_use', '=', 'purchase'), ('company_id', '=', line.company_id.id)], limit=1)
                line.order_id.order_line.filtered('axx_is_rc_relevant').write({'taxes_id': [(6, 0, [tax_id.id])]})
            elif line.axx_is_rc_relevant and \
                    sum(line.order_id.order_line.filtered('axx_is_rc_relevant').mapped('price_subtotal')) < 5000:
                line._compute_tax_id()
            else:
                line._compute_tax_id()

    @api.onchange('product_id')
    def onchange_rc_related(self):
        for line in self:
            if line.product_id:
                line.axx_is_rc_relevant = line.product_id.categ_id.axx_is_rc_relevant
                line.axx_is_additional_service = line.product_id.categ_id.axx_is_additional_service
