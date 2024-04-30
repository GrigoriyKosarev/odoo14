from odoo import fields, models, _, api
from odoo.exceptions import UserError, ValidationError
import re


class TestWizard(models.TransientModel):
    _name = 'gk.test.wizard'

    test_field = fields.Char()
    test_product_id = fields.Many2one(comodel_name='product.product', string='product.product')
    test_product_template_id = fields.Many2one(comodel_name='product.template', string='Product template', default=6330) #6396
    web_table_stock_value = fields.Html()

    def set_web_table_stock_value(self):
        # product_ids = self.env['product.product'].search_read()
        self.web_table_stock_value = self.test_product_template_id.get_web_table_stock_value()

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'gk.test.wizard',
            'target': 'new',
            'res_id': self.id,
        }

    def apply_action(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'gk.test.wizard',
            'target': 'new',
            'res_id': self.id,
        }

    def test_action(self):
        # work_order_id = self.env['mrp.production'].search([['id', '=', 5492]])
        # for el in work_order_id.workorder_ids:
        #     name = el.name

        # product_template_id = self.env['product.template'].browse(6379)
        # product_template_id.free_stock_quant()

        # self.env['product.template'].set_stock_quant_ml()
        # result = self.test_product_template_id.get_product_tmpl_stock_attributes()
        # self.test_product_template_id.set_stock_attributes(self.test_product_template_id.id)

        attribute_id = 36
        attribute_value = 1165

        product_template_ids = self.env['product.template'].search([('allow_out_of_stock_order', '=', False)])

        for product_template in product_template_ids:
            # product_template = env['product.template'].browse([19434])
            attribute_line = product_template.attribute_line_ids.filtered(lambda l: l.attribute_id.id == attribute_id)

            if attribute_line:
                if attribute_value not in attribute_line.value_ids.ids:
                    attribute_line.write({'value_ids': [(4, attribute_value)]})
            else:
                product_template.write({
                    'attribute_line_ids': [(0, 0, {'attribute_id': attribute_id, 'value_ids': [(4, attribute_value)]})]
                })

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'gk.test.wizard',
            'target': 'new',
            'res_id': self.id,
        }

    def action_open_wizard(self):

        # quants = self.env['stock.quant'].search([('location_id', '=', 131)])
        # product_tmpl_ids  = quants.mapped('product_id.product_tmpl_id')


        view_id = self.env.ref(
            'gk_test.view_gk_test_form')  # Замініть module_name на ваш модуль та view_gk_test_form на вашу відповідну ID перегляду
        return {
            'name': _('TEST Wizard'),
            # 'name': 'Create Partners Wizard',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'views': [(view_id.id, 'form')],
            'res_model': 'gk.test.wizard',
            'target': 'new',
            # 'context': self._context,
            'context': {
                'default_test_field': self.test_field,
                'default_test_product_id': self.test_product_id.id,
                'form_view_ref': 'module_name.view_gk_test_form',  # Замініть module_name на ваш модуль та view_gk_test_form на вашу відповідну ID перегляду
                'on_close': 'apply_action',  # Викликати метод apply_action при закритті вікна
            },
            # 'context': {'default_country_id': self.env.user.company_id.id},
        }


    def get_eu_size(self, size):
        pattern = r'\b(\d+)eu\b'  # Шаблон для числового значення, яке має після себе "eu"

        matches = re.findall(pattern, size)
        if matches:
            return matches[0] # Виведе: 36
        return ""

    def add_additional_barcodes_action(self):

        product_ids = self.env['product.product'].search_read()
        for product_id in product_ids:
            # product_id = self.test_product_id
            product_tmpl_ids = self.env['product.template'].search_read([['id', '=', product_id['product_tmpl_id'][0]]])
            if product_tmpl_ids == 0:
                continue
            name_tmpl = product_tmpl_ids[0]['name']
            search_term_lst = []
            search_term_lst.append("*")
            search_term_lst.append(name_tmpl)
            res = self.get_product_attribute_color_size_value(product_id)
            if res['color']:
                search_term_lst.append(res['color'][0].lower())
            if res['size']:
                search_term_lst.append(self.get_eu_size(res['size']))

            search_term = "".join(search_term_lst)
            barcode_ids = self.env['product.barcode.multi'].search_read([
                ['product_id', '=', product_id['id']],
                ['name', '=', search_term]])
            if len(barcode_ids) == 0:
                self.env['product.barcode.multi'].create({
                    'product_id': product_id['id'],
                    'name': search_term
                })
            # print(search_term)


    def get_product_attribute_color_size_value(self, product_id):
        color_id = 2
        size_id = 4
        # product_product = self.env['product.product'].browse(product_id)

        color_value = False
        size_value = False

        # product_tmpl_ids = self.env['product.attribute.value'].search_read([['attribute_id', '=', color_id],['attribute_id', '=', product_id]])

        for prod_tmpl_att_value_id in product_id['product_template_variant_value_ids']:
            prod_tmpl_att_value = self.env['product.template.attribute.value'].browse(prod_tmpl_att_value_id)
            if prod_tmpl_att_value.attribute_id.id == color_id:
                color_value = prod_tmpl_att_value.name
            elif prod_tmpl_att_value.attribute_id.id == size_id:
                size_value = prod_tmpl_att_value.name

        return {
            'color': color_value,
            'size': size_value
        }

