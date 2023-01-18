from odoo import api, fields, models, _
import copy


class AxxSaleOrder(models.Model):
    _inherit = 'sale.order'

    axx_is_active_rc = fields.Boolean(string='Is RC Active', default=True)

    def additional_service_validation(self, line, rc_relevant_total):
        lines_to_delete = []
        price = 0
        if rc_relevant_total > 5000:
            non_rc_relevant_total = sum(self.order_line.filtered(
                lambda line_id: not line_id.axx_is_rc_relevant and
                                not line_id.axx_is_additional_service).mapped('price_subtotal'))
            if non_rc_relevant_total:
                additional_service_total = non_rc_relevant_total
            elif line.axx_is_rc_relevant:
                additional_service_total = sum(line.order_id.order_line.filtered(
                    lambda rec: rec.product_id.id == line.product_id.id).mapped('price_unit'))
            else:
                additional_service_total = line.price_subtotal
            if not line.axx_is_rc_calculation_done:
                if (self.amount_untaxed - additional_service_total) == rc_relevant_total:
                    line.write({'axx_is_rc_relevant': True, 'axx_is_rc_calculation_done': True})
                else:
                    rc_relevant_perc = (rc_relevant_total / self.amount_untaxed)
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
                if (self.amount_untaxed - additional_service_total) == rc_relevant_total:
                    price = sum(line.order_id.order_line.filtered(
                        lambda rec: rec.product_id.id == line.product_id.id).mapped('price_unit'))
                    line.write({'price_unit': price, 'axx_is_rc_calculation_done': False})
                elif non_rc_relevant_total:
                    rc_relevant_perc = (rc_relevant_total / self.amount_untaxed)
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
        return lines_to_delete

    def update_so_line_tax(self, line, rc_relevant_total):
        if line.axx_is_rc_relevant and rc_relevant_total > 5000:
            tax_id = self.env['account.tax'].search(
                [('name', '=ilike', '0% Umsatzsteuer Lieferung von Mobilfunkgeräten u.a. (§13b)'),
                 ('type_tax_use', '=', 'sale'), ('company_id', '=', line.company_id.id)], limit=1)
            line.order_id.order_line.filtered('axx_is_rc_relevant').write({'tax_id': tax_id})
        elif line.axx_is_rc_relevant and rc_relevant_total < 5000:
            line.order_id.order_line.filtered('axx_is_rc_relevant')._compute_tax_id()
        else:
            line._compute_tax_id()

    def reverse_charge_validation(self):
        for order in self.filtered(lambda so: so.axx_is_active_rc):
            lines_to_delete = []
            for line in order.order_line:
                rc_relevant_total = sum(order.order_line.filtered(
                    lambda line_id: line_id.axx_is_rc_relevant and
                                    not line_id.axx_is_additional_service).mapped('price_subtotal'))
                if line.axx_is_additional_service:
                    lines_to_delete = order.additional_service_validation(line, rc_relevant_total)
                order.update_so_line_tax(line, rc_relevant_total)
            lines_to_delete and [order_line.unlink() for order_line in lines_to_delete]
        for order in self.filtered(lambda so: not so.axx_is_active_rc):
            order.order_line.filtered('axx_is_rc_relevant')._compute_tax_id()

    def write(self, vals):
        res = super(AxxSaleOrder, self).write(vals)
        self.reverse_charge_validation()
        return res


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
            if line.axx_is_rc_relevant and \
                    sum(line.order_id.order_line.filtered('axx_is_rc_relevant').mapped('price_subtotal')) > 5000:
                tax_id = self.env['account.tax'].search(
                    [('name', '=ilike', '0% Umsatzsteuer Lieferung von Mobilfunkgeräten u.a. (§13b)'),
                     ('type_tax_use', '=', 'sale'), ('company_id', '=', line.company_id.id)], limit=1)
                line.tax_id = tax_id
            elif line.axx_is_rc_relevant and \
                    sum(line.order_id.order_line.filtered('axx_is_rc_relevant').mapped('price_subtotal')) < 5000:
                super(AxxSaleOrderLine, self)._compute_tax_id()
            else:
                super(AxxSaleOrderLine, self)._compute_tax_id()

    @api.onchange('product_uom_qty', 'price_unit')
    def axx_onchange_subtotal(self):
        for line in self:
            if line.axx_is_rc_relevant and \
                    sum(line.order_id.order_line.filtered('axx_is_rc_relevant').mapped('price_subtotal')) > 5000:
                tax_id = self.env['account.tax'].search(
                    [('name', '=ilike', '0% Umsatzsteuer Lieferung von Mobilfunkgeräten u.a. (§13b)'),
                     ('type_tax_use', '=', 'sale'), ('company_id', '=', line.company_id.id)], limit=1)
                line.tax_id = tax_id
            elif line.axx_is_rc_relevant and \
                    sum(line.order_id.order_line.filtered('axx_is_rc_relevant').mapped('price_subtotal')) < 5000:
                line._compute_tax_id()
            else:
                line._compute_tax_id()