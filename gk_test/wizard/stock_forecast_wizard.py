from collections import defaultdict

from odoo import fields, api, models, _
from odoo.tools import float_compare, float_is_zero, format_date, float_round

class StockForecastWizard(models.TransientModel):
    _name = 'gk.stock.forecast.wizard'

    test_field = fields.Char()
    test_product_id = fields.Many2one(comodel_name='product.product', string='product.product')

    def apply_action(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'gk.stock.forecast.wizard',
            'target': 'new',
            'res_id': self.id,
        }

    def action_open_wizard1(self):
        view_id = self.env.ref(
            'gk_test.view_gk_stock_forecast_wizard_form')  # Замініть module_name на ваш модуль та view_gk_test_form на вашу відповідну ID перегляду
        return {
            'name': _('TEST Wizard'),
            # 'name': 'Create Partners Wizard',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'views': [(view_id.id, 'form')],
            'res_model': 'gk.stock.forecast.wizard',
            'target': 'new',
            # 'context': self._context,
            'context': {
                'default_test_field': self.test_field,
                'default_test_product_id': self.test_product_id.id,
                'form_view_ref': 'module_name.view_gk_stock_forecast_wizard_form',  # Замініть module_name на ваш модуль та view_gk_test_form на вашу відповідну ID перегляду
                'on_close': 'apply_action',  # Викликати метод apply_action при закритті вікна
            },
            # 'context': {'default_country_id': self.env.user.company_id.id},
        }

    def get_stock_forecast(self):
        web_descr = """
                            <table style="font-family: Roboto; margin-left: auto;margin-right: auto;">
                				<tbody>
                					<tr bgcolor="#E9ECEF" align="center">
                			       	<td style="border: 1px solid #c6c6c6;font-size:14.0pt;padding:10pt"><b>Size | Color</b></td>
                			           <td style="border: 1px solid #c6c6c6;font-size:14.0pt;padding:10pt"><b>Q-ty</b></td>
                			           <td style="border: 1px solid #c6c6c6;font-size:14.0pt;padding:10pt"><b>Delivery</b></td>
                					</tr>
                            """
        stock = "3-4 weeks"
        web_descr_td = ""

        wh_location_ids = [loc['id'] for loc in self.env['stock.location'].search_read(
            [('id', 'child_of', 8)],
            ['id'],
        )]
        # product_template_ids = self.env['product.template'].search([['id', '=', 48]])
        product_template_ids = self.env['product.template'].search([])
        # docs['virtual_available'] + docs['qty']['in'] - docs['qty']['out']
        for product_tmpl_id in product_template_ids:
            add_descr = False
            web_descr_td = ""
            for product_id in product_tmpl_id['product_variant_ids']:
                product_variant_ids = [product_id]
                res = {}
                product_variants = self.env['product.product'].browse(product_variant_ids)
                res['product_templates'] = False
                res['product_variants'] = product_variants
                res['multiple_product'] = len(product_variants) > 1
                # res['uom'] = product_variants[:1].uom_id.display_name
                # res['quantity_on_hand'] = sum(product_variants.mapped('qty_available'))
                # res['virtual_available'] = sum(product_variants.mapped('virtual_available'))
                res['uom'] = product_id.uom_id.display_name
                res['quantity_on_hand'] = product_id.qty_available
                res['virtual_available'] = product_id.virtual_available

                res.update(self._compute_draft_quantity_count(product_template_ids, product_variant_ids, wh_location_ids))
                res['lines'] = self._get_report_lines(product_template_ids, product_variant_ids, wh_location_ids)
                forecasted_plus_padding = res['virtual_available'] + res['qty']['in'] - res['qty']['out']
                product_tmpl_name =  product_tmpl_id['name']
                display_name = product_id['display_name']

                if forecasted_plus_padding > 0:
                    add_descr = True
                    web_descr_td = f'{web_descr_td}' \
                                   f'<tr align="center">' \
                                   f'<td style="border: 1px solid #c6c6c6;font-size:10.0pt;padding:10pt">{display_name}</td>' \
                                   f'<td style="border: 1px solid #c6c6c6;font-size:10.0pt;padding:10pt">{forecasted_plus_padding}</td>' \
                                   f'<td style="border: 1px solid #c6c6c6;font-size:10.0pt;padding:10pt">{stock}</td>' \
                                   f'</tr>'

            web_descr_result = f'{web_descr} {web_descr_td} </tbody> </table>'
            product_tmpl_id.write({'public_description': web_descr_result if add_descr else ""})

        pass

    def _product_domain(self, product_template_ids, product_variant_ids):
        # if product_template_ids:
        #     return [('product_tmpl_id', 'in', product_template_ids)]
        # return [('product_id', 'in', product_variant_ids)]
        return [('product_id', '=', product_variant_ids[0].id)]

    def _move_domain(self, product_template_ids, product_variant_ids, wh_location_ids):
        move_domain = self._product_domain(product_template_ids, product_variant_ids)
        move_domain += [('product_uom_qty', '!=', 0)]
        out_domain = move_domain + [
            '&',
            ('location_id', 'in', wh_location_ids),
            ('location_dest_id', 'not in', wh_location_ids),
        ]
        in_domain = move_domain + [
            '&',
            ('location_id', 'not in', wh_location_ids),
            ('location_dest_id', 'in', wh_location_ids),
        ]
        return in_domain, out_domain
        # return move_domain, move_domain

    def _move_draft_domain(self, product_template_ids, product_variant_ids, wh_location_ids):
        in_domain, out_domain = self._move_domain(product_template_ids, product_variant_ids, wh_location_ids)
        in_domain += [('state', '=', 'draft')]
        out_domain += [('state', '=', 'draft')]
        return in_domain, out_domain

    def _move_confirmed_domain(self, product_template_ids, product_variant_ids, wh_location_ids):
        in_domain, out_domain = self._move_domain(product_template_ids, product_variant_ids, wh_location_ids)
        out_domain += [('state', 'in', ['waiting', 'assigned', 'confirmed', 'partially_available'])]
        in_domain += [('state', 'in', ['waiting', 'assigned', 'confirmed', 'partially_available'])]
        return in_domain, out_domain

    def _compute_draft_quantity_count(self, product_template_ids, product_variant_ids, wh_location_ids):
        in_domain, out_domain = self._move_draft_domain(product_template_ids, product_variant_ids, wh_location_ids)
        incoming_moves = self.env['stock.move'].read_group(in_domain, ['product_qty:sum'], 'product_id')
        # test_in_domain = [('product_id', '=', 83)]
        # incoming_moves = self.env['stock.move'].read_group(test_in_domain, ['product_id'], 'product_id')
        outgoing_moves = self.env['stock.move'].read_group(out_domain, ['product_qty:sum'], 'product_id')
        in_sum = sum(move['product_qty'] for move in incoming_moves)
        out_sum = sum(move['product_qty'] for move in outgoing_moves)
        return {
            'draft_picking_qty': {
                'in': in_sum,
                'out': out_sum
            },
            'qty': {
                'in': in_sum,
                'out': out_sum
            }
        }

    def _get_report_lines(self, product_template_ids, product_variant_ids, wh_location_ids):

        def _reconcile_out_with_ins(lines, out, ins, demand, product_rounding, only_matching_move_dest=True):
            index_to_remove = []
            for index, in_ in enumerate(ins):
                if float_is_zero(in_['qty'], precision_rounding=product_rounding):
                    index_to_remove.append(index)
                    continue
                if only_matching_move_dest and in_['move_dests'] and out.id not in in_['move_dests']:
                    continue
                taken_from_in = min(demand, in_['qty'])
                demand -= taken_from_in
                lines.append(self._prepare_report_line(taken_from_in, move_in=in_['move'], move_out=out))
                in_['qty'] -= taken_from_in
                if in_['qty'] <= 0:
                    index_to_remove.append(index)
                if float_is_zero(demand, precision_rounding=product_rounding):
                    break
            for index in reversed(index_to_remove):
                del ins[index]
            return demand

        in_domain, out_domain = self._move_confirmed_domain(
            product_template_ids, product_variant_ids, wh_location_ids
        )
        outs = self.env['stock.move'].search(out_domain, order='reservation_date, priority desc, date, id')
        outs_per_product = defaultdict(list)
        reserved_outs = self.env['stock.move']
        reserved_outs_quantitites = defaultdict(float)
        reserved_outs_per_product = defaultdict(list)
        outs_reservation = {}
        for out in outs:
            outs_per_product[out.product_id.id].append(out)
            out_qty_reserved = 0
            moves_orig = out._get_moves_orig()
            for move in moves_orig:
                rounding = move.product_id.uom_id.rounding
                move_qty_reserved = sum(move.move_line_ids.mapped('product_qty'))
                if float_is_zero(move_qty_reserved, precision_rounding=rounding):
                    continue
                already_used_qty = reserved_outs_quantitites.get(move, 0)
                remaining_qty = move_qty_reserved - already_used_qty
                if float_compare(remaining_qty, 0, precision_rounding=rounding) <= 0:
                    continue
                qty_reserved = min(remaining_qty, out.product_qty - out_qty_reserved)
                out_qty_reserved += qty_reserved
                reserved_outs_quantitites[move] += qty_reserved
                if float_compare(out_qty_reserved, out.product_qty, precision_rounding=rounding) >= 0:
                    break
            if not float_is_zero(out_qty_reserved, out.product_id.uom_id.rounding):
                reserved_outs |= out
                reserved_outs_per_product[out.product_id.id].append(out)
                outs_reservation[out.id] = out_qty_reserved
        # Different sort than unreserved outs
        reserved_outs = self.env['stock.move'].search([('id', 'in', reserved_outs.ids)], order="priority desc, date, id")
        ins = self.env['stock.move'].search(in_domain, order='priority desc, date, id')
        ins_per_product = defaultdict(list)
        for in_ in ins:
            ins_per_product[in_.product_id.id].append({
                'qty': in_.product_qty,
                'move': in_,
                'move_dests': in_._rollup_move_dests(set())
            })
        currents = outs.product_id._get_only_qty_available()

        lines = []
        for product in (ins | outs).product_id:
            product_rounding = product.uom_id.rounding
            for out in reserved_outs_per_product[product.id]:
                # Reconcile with reserved stock.
                reserved = outs_reservation[out.id]
                current = currents[product.id]
                currents[product.id] -= reserved
                lines.append(self._prepare_report_line(reserved, move_out=out, reservation=True))

            unreconciled_outs = []
            for out in outs_per_product[product.id]:
                reserved_availability = outs_reservation.get(out.id, 0)
                # Reconcile with the current stock.
                reserved = 0.0
                if not float_is_zero(reserved_availability, precision_rounding=product_rounding):
                    reserved = reserved_availability
                demand = out.product_qty - reserved

                if float_is_zero(demand, precision_rounding=product_rounding):
                    continue
                current = currents[product.id]
                taken_from_stock = min(demand, current)
                if not float_is_zero(taken_from_stock, precision_rounding=product_rounding):
                    currents[product.id] -= taken_from_stock
                    demand -= taken_from_stock
                    lines.append(self._prepare_report_line(taken_from_stock, move_out=out))
                # Reconcile with the ins.
                if not float_is_zero(demand, precision_rounding=product_rounding):
                    demand = _reconcile_out_with_ins(lines, out, ins_per_product[product.id], demand, product_rounding, only_matching_move_dest=True)
                if not float_is_zero(demand, precision_rounding=product_rounding):
                    unreconciled_outs.append((demand, out))

            # Another pass, in case there are some ins linked to a dest move but that still have some quantity available
            for (demand, out) in unreconciled_outs:
                demand = _reconcile_out_with_ins(lines, out, ins_per_product[product.id], demand, product_rounding, only_matching_move_dest=False)
                if not float_is_zero(demand, precision_rounding=product_rounding):
                    # Not reconciled
                    lines.append(self._prepare_report_line(demand, move_out=out, replenishment_filled=False))
            # Unused remaining stock.
            free_stock = currents.get(product.id, 0)
            if not float_is_zero(free_stock, precision_rounding=product_rounding):
                lines.append(self._prepare_report_line(free_stock, product=product))
            # In moves not used.
            for in_ in ins_per_product[product.id]:
                if float_is_zero(in_['qty'], precision_rounding=product_rounding):
                    continue
                lines.append(self._prepare_report_line(in_['qty'], move_in=in_['move']))
        return lines

    def _prepare_report_line(self, quantity, move_out=None, move_in=None, replenishment_filled=True, product=False, reservation=False):
        product = product or (move_out.product_id if move_out else move_in.product_id)
        is_late = move_out.date < move_in.date if (move_out and move_in) else False

        move_to_match_ids = self.env.context.get('move_to_match_ids') or []
        move_in_id = move_in.id if move_in else None
        move_out_id = move_out.id if move_out else None

        return {
            'document_in': move_in._get_source_document() if move_in else False,
            'document_out': move_out._get_source_document() if move_out else False,
            'product': {
                'id': product.id,
                'display_name': product.display_name
            },
            'replenishment_filled': replenishment_filled,
            'uom_id': product.uom_id,
            'receipt_date': format_date(self.env, move_in.date) if move_in else False,
            'delivery_date': format_date(self.env, move_out.date) if move_out else False,
            'is_late': is_late,
            'quantity': float_round(quantity, precision_rounding=product.uom_id.rounding),
            'move_out': move_out,
            'move_in': move_in,
            'reservation': reservation,
            'is_matched': any(move_id in [move_in_id, move_out_id] for move_id in move_to_match_ids),
        }

