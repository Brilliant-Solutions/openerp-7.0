# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2010-2013 Elico Corp. All Rights Reserved.
#    Author: Qiao Lei <qiao.lei@elico-corp.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import fields, osv, orm
import openerp.addons.decimal_precision as dp
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT,
                           DEFAULT_SERVER_DATETIME_FORMAT,
                           DATETIME_FORMATS_MAP, float_compare)
from openerp.tools.float_utils import float_round
import logging
_logger = logging.getLogger(__name__)


def float_eq(f1, f2, precision):
    # if float_round(f1, precision) - float_round(f2, precision) == 0.0:
    float_diff = float_round(f1 - f2, precision + 1)
    float_allow = 0.5 / pow(10, precision)
    if (float_diff <= float_allow and float_diff >= -float_allow):
        return True
    else:
        return False


class product_template(orm.Model):
    _inherit = "product.template"
    _columns = {
        'minimum_price': fields.float(
            'Minimum Price', required=True,
            digits_compute=dp.get_precision('Product Price'),),
    }
    _defaults = {
        'minimum_price': 0.00,
    }


class sale_order_line(orm.Model):
    _inherit = 'sale.order.line'

    def _check_price(self, cr, uid, ids, context=None):
        precision = self.pool.get('decimal.precision').precision_get(
            cr, uid, 'Account')
        for sol in self.browse(cr, uid, ids, context=context):
            price_unit = sol.price_unit
            original_price = sol.original_price
            if original_price != 0:
                computed_discount_dummy = float_round(
                    (float(original_price) - price_unit) / original_price * 100, precision)
                if ((original_price != 0) and
                    (not sol.sample) and
                        (not float_eq(sol.discount_dummy, computed_discount_dummy, precision))):
                    _logger.debug("X: discount/100 != (original_price-final_price)/original_price, precision)"
                                  "\n%s != %s, precision : %s" % (sol.discount_dummy, computed_discount_dummy, precision))
                    return False
        return True

    def _get_original_price_2(
            self, cr, uid, ids, fields_name, arg=None, context=None):
        res = {}
        for sol in self.browse(cr, uid, ids, context=context):
            res[sol.id] = sol.original_price
        return res
    def _check_uom_category(self, cr, uid, ids, context=None):

        for sol in self.browse(cr, uid, ids, context=context):
            product_uom = sol.product_uom or None
            product_id = sol.product_id or None
            if product_id and product_uom and product_id.uom_id.category_id != product_uom.category_id:
                return False
        return True

    _columns = {
        'original_price_2': fields.function(
            _get_original_price_2, arg=None, type='float',
            string='Original Price', digits_compute=dp.get_precision('Account'),
            help='same as price_unit, but readonly'),
        'original_price': fields.float(
            'Original Price', digits_compute=dp.get_precision('Product Price')),
        # change the string of unit price to final price.
        'price_unit': fields.float(
            'Final Price', required=True,
            digits_compute=dp.get_precision('Product Price'), readonly=True,
            states={'draft': [('readonly', False)]}),
        'discount_dummy': fields.float(
            'Disc.(%)',
            digits_compute=dp.get_precision('Discount')),
    }

    _defaults = {
        'discount': 0.0,
    }
    _constraints = [
        (_check_uom_category, 'Error! The UoM category of the line and product are not the same ',
            ['product_uom', 'product_id'])
    ]
    # _constraints = [
    #     (_check_price, 'Error! Unit-Price X Discount != Final Price ',
    #         ['discount_dummy', 'original_price', 'price_unit', 'sample'])
    # ]

    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):
        res = super(sale_order_line, self)._prepare_order_line_invoice_line(
            cr, uid, line, account_id=account_id, context=context)
        res['discount'] = 0.00
        res['discount_dummy'] = line.discount_dummy
        res['original_price'] = line.original_price
        return res

    def product_id_change(
        self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False,
            fiscal_position=False, flag=False, context=None):
        res = super(sale_order_line, self).product_id_change(
            cr, uid, ids, pricelist, product, qty=qty,
            uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id,
            lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging,
            fiscal_position=fiscal_position, flag=flag, context=context)

        price_unit = res['value'].get('price_unit', 0.0)
        if flag:
            return res
        if context.get('sample', False):
            discount_dummy = 100
            price_unit = 0
        else:
            price_unit = price_unit
            discount_dummy = 0.0
        res['value'].update(
            {'discount_dummy': discount_dummy, 'original_price': price_unit, 'original_price_2': price_unit, 'price_unit': price_unit})
        return res

    def compute_unit_price_discount_dummy(
            self, cr, uid, ids, type, sample, original_price, discount_dummy, price_unit):
        res = {}
        precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        dis_precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Discount')
        if sample:
            res.update({'discount_dummy': 100, 'price_unit': 0.0})
            return res
        if original_price == 0.0:
            res.update({'discount_dummy': 0, 'price_unit': price_unit})
            return res
        if type == 'discount_dummy':
            price_unit = float_round((float(original_price) * (100 - discount_dummy) / 100), precision)
            res.update({'price_unit': price_unit, 'discount_dummy': discount_dummy})
        else:
            discount_dummy = float_round(((original_price - price_unit) / float(original_price)) * 100, dis_precision)
            res.update({'discount_dummy': discount_dummy, 'price_unit': price_unit})
        return res

    def discount_dummy_change(
            self, cr, uid, ids, original_price, discount_dummy, price_unit, sample, context=None):
        res = self.compute_unit_price_discount_dummy(
            cr, uid, ids, 'discount_dummy', sample, original_price, discount_dummy, price_unit)
        return {'value': res}

    def price_unit_change(
            self, cr, uid, ids, original_price, discount_dummy, price_unit, sample, context=None):
        res = self.compute_unit_price_discount_dummy(
            cr, uid, ids, 'price_unit', sample, original_price, discount_dummy, price_unit)
        return {'value': res}


class account_invoice_line(orm.Model):
    _inherit = 'account.invoice.line'

    _columns = {
        'discount_dummy': fields.float(
            'Disc. SO(%)',
            digits_compute=dp.get_precision('Discount'),
            readonly=True),
        'original_price': fields.float(
            'Original Price', digits_compute=dp.get_precision('Product Price'), readonly=True),
        'price_unit': fields.float(
            'Final Price', required=True, digits_compute=dp.get_precision('Product Price')),
        'discount': fields.float('Disc.(%)', digits_compute=dp.get_precision('Discount')),
    }


class account_invoice_tax(orm.Model):
    _inherit = 'account.invoice.tax'

    def compute_str(self, cr, uid, invoice_id, context=None):
        return repr(self.compute(cr, uid, invoice_id, context=context))


class stock_picking(osv.osv):
    _inherit = 'stock.picking'

    def _prepare_invoice_line(self, cr, uid, group, picking, move_line, invoice_id,
                              invoice_vals, context=None):
        res = super(stock_picking, self)._prepare_invoice_line(
            cr, uid, group, picking, move_line, invoice_id,
            invoice_vals, context=context)
        if move_line and move_line.sale_line_id:
            res['discount'] = 0.00
            res['discount_dummy'] = move_line.sale_line_id.discount_dummy
            res['original_price'] = move_line.sale_line_id.original_price
        return res

#ref 2818 Add UOM contraint
class purchase_order_line(osv.osv):
    _inherit = 'purchase.order.line'
    def _check_uom_category(self, cr, uid, ids, context=None):

        for pol in self.browse(cr, uid, ids, context=context):
            product_uom = pol.product_uom or None
            product_id = pol.product_id or None
            if product_id and product_uom and product_id.uom_id.category_id != product_uom.category_id:
                return False
        return True
    _constraints = [
        (_check_uom_category, 'Error! The UoM category of the line and product are not the same ',
            ['product_uom', 'product_id'])
    ]

class stock_move(osv.osv):
    _inherit = 'stock.move'
    def _check_uom_category(self, cr, uid, ids, context=None):

        for move in self.browse(cr, uid, ids, context=context):
            product_uom = move.product_uom or None
            product_id = move.product_id or None
            if product_id and product_uom and product_id.uom_id.category_id != product_uom.category_id:
                return False
        return True
    _constraints = [
        (_check_uom_category, 'Error! The UoM category of the line and product are not the same ',
            ['product_uom', 'product_id'])
    ]

