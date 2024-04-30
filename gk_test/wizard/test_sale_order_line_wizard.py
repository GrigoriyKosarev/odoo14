from odoo import fields, models, _, api
from odoo.exceptions import UserError, ValidationError
import re


class TestSaleOrderLineWizard(models.TransientModel):
    _name = 'gk.sale.order.line.test.wizard'

    test_field = fields.Char()
    order_id = fields.Integer(string='Order id', default=11766)

    def apply_action(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'gk.sale.order.line.test.wizard',
            'target': 'new',
            'res_id': self.id,
        }

    def set_lot_action(self):
        order_line_ids = self.env['sale.order.line'].search([['order_id', '=', self.order_id]])
        for order_line in order_line_ids:
            for move_id in order_line.move_ids:
                if move_id.created_production_id:
                    lot_producing_id = move_id.created_production_id.lot_producing_id
                    if lot_producing_id:
                        lot_id = lot_producing_id.id
                        order_line.with_context(skip_validation=True).write({'lot_id': lot_id})
                        # order_line.sudo().write({'lot_id': lot_id})

    def action_open_wizard(self):
        view_id = self.env.ref(
            'gk_test.view_gk_sale_order_line_test_wizard_form')
        return {
            'name': _('TEST Wizard'),
            # 'name': 'Create Partners Wizard',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'views': [(view_id.id, 'form')],
            'res_model': 'gk.sale.order.line.test.wizard',
            'target': 'new',
            # 'context': self._context,
            'context': {
                'default_test_field': self.test_field,
                # 'form_view_ref': 'module_name.view_gk_test_form',  # Замініть module_name на ваш модуль та view_gk_test_form на вашу відповідну ID перегляду
                'on_close': 'apply_action',  # Викликати метод apply_action при закритті вікна
            },
            # 'context': {'default_country_id': self.env.user.company_id.id},
        }