# -*- coding: utf-8 -*-
##############################################################################
#
#    Alphasoft Solusi Integrasi, PT
#    Copyright (C) 2014 Alphasoft (<https://www.alphasoft.co.id/>).
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

from lxml import etree
from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import odoo.addons.decimal_precision as dp

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    fp_export = fields.Boolean(string="OB Is Exported")
    fp_date = fields.Datetime(string="OB Exported Date", required=False)
    
class account_invoice(models.Model):
    _inherit    = "account.invoice"
    
    @api.one
    @api.depends('nomor_faktur_id', 'nomor_faktur_id.name', 'state', 
                 #'partner_id.code_transaction', 'partner_id.ktp', 'partner_id.npwp', 'partner_id.is_npwp', 'partner_id.fp_export'
                 )
    def _nomor_faktur_partner(self):
        for invoice in self:
            invoice.nomor_faktur_partner = "%s.%s" % (invoice.partner_id.code_transaction,invoice.nomor_faktur_id and invoice.nomor_faktur_id.name)
            invoice.code_transaction = invoice.partner_id.code_transaction
            invoice.npwp_no = invoice.partner_id._get_no_npwp() and invoice.partner_id._get_no_npwp()[0] or invoice.partner_id.npwp or '00.000.000.0-000.000'
            invoice.ktp = invoice.partner_id.ktp
            if invoice.npwp_no:
                npwp = invoice.npwp_no
                npwp = npwp.replace('.','')
                npwp = npwp.replace('-','')
                invoice.npwp_efaktur = npwp
    
    @api.depends('amount_tax')
    def _get_is_taxed(self):
        for invoice in self:
            invoice.is_taxed = False
            if invoice.amount_tax:
                invoice.is_taxed = True

    is_taxed = fields.Boolean(string='Is Taxed', compute='_get_is_taxed')
    fp_export = fields.Boolean(string="FP Is Exported")
    fp_date = fields.Datetime(string="FP Exported Date", required=False)
    nomor_faktur_id = fields.Many2one('nomor.faktur.pajak', string='Nomor Faktur Pajak', change_default=True, copy=False)
    code_transaction = fields.Selection([
            ('01','010.'),('02','020.'),('03','030.'),('07','070'),('08','080.')
        ], string='Kode Faktur', compute='_nomor_faktur_partner', store=True, readonly=True)
    nomor_faktur_partner = fields.Char(string='Nomor Faktur', digits=dp.get_precision('Account'),
        store=True, readonly=True, compute='_nomor_faktur_partner')
    ktp = fields.Char(string='NIK', compute='_nomor_faktur_partner', store=True, readonly=True)
    npwp_no = fields.Char(string='NPWP', compute='_nomor_faktur_partner', store=True, readonly=True)
    npwp_efaktur = fields.Char(string='NPWP for eFaktur', compute='_nomor_faktur_partner', store=False, readonly=True)
    non_faktur_pajak = fields.Boolean(string='Non-FP', help='This option will not take faktur pajak automatically')
    vat_supplier = fields.Char(string='Faktur Pajak No', size=63, readonly=True, states={'draft': [('readonly', False)]}, index=True,
        help="Nomor Bukti Potong", copy=False)
    
#     @api.multi
#     def write(self, vals):
#         if vals.get('nomor_faktur_id', False):
#             faktur = self.env['nomor.faktur.pajak'].browse(vals['nomor_faktur_id'])
#             if self.type == 'out_invoice':
#                 faktur.write({'invoice_id': self.id})
#             elif self.type == 'out_refund':
#                 faktur.write({'refund_invoice_id': self.id})
#         return super(account_invoice, self).write(vals)
    
    @api.multi
    def onchange_partner_npwp(self, npwp=False):
        return {'value': {}}
    
    @api.multi
    def action_faktur_unused(self):
        for inv in self:
            # Here the onchange will automatically write to the database
            if inv.nomor_faktur_id:
                inv.nomor_faktur_id = False
        return True
    
    @api.multi
    def action_invoice_cancel(self):
        # lots of duplicate calls to action_invoice_open, so we remove those already open
        if self.filtered(lambda inv: inv.state not in ['draft', 'open']):
            raise UserError(_("Invoice must be in draft or open state in order to be cancelled."))
        self.action_faktur_unused()
        return self.action_cancel()
    
#     @api.multi
#     def action_move_create(self):
#         result = super(account_invoice, self).action_move_create()
#         if self.amount_tax and not self.non_faktur_pajak:
#             self.faktur_pajak_create()
#         return result
    
    @api.multi
    def action_move_create(self):
        result = super(account_invoice, self).action_move_create()
        for inv in self:
            if inv.amount_tax and not inv.non_faktur_pajak:
                inv.faktur_pajak_create()
        return result

    
    @api.one
    def faktur_pajak_create(self):
        if not self.nomor_faktur_id and self.type == 'out_invoice' and self.company_id.efaktur_automatic:
            obj_no_faktur = self.env['nomor.faktur.pajak'].search([('type','=','out'),('state','=','0'),('invoice_id','=',False),('fp_company_id','=',self.company_id.id)], limit=1)
            if obj_no_faktur:
                if self.type == 'out_invoice':
                    obj_no_faktur.write({'invoice_id': self.id})
                self.nomor_faktur_id = obj_no_faktur.id
            else:
                raise UserError(_('No Faktur Pajak Keluaran found!\nPlease Generate Faktur Pajak Keluaran first!'))
        elif self.nomor_faktur_id:
            obj_no_faktur = self.env['nomor.faktur.pajak'].browse(self.nomor_faktur_id.id)
            if self.nomor_faktur_id and self.type in ('out_invoice','in_invoice'):
                self.nomor_faktur_id.write({'invoice_id': self.id})
#             elif self.nomor_faktur_id and self.type == 'in_invoice':                
#                 if self.nomor_faktur_id[3] == "." and self.nomor_faktur_id[6] == '.':
#                     if len(str(self.nomor_faktur_id).split('.')[2]) > 8: 
#                         raise UserError(_('Wrong Faktur Number'), _('Nomor Urut max 8 Digit'))               
#                     vals = {
#                         'nomor_perusahaan'  : str(self.vat_supplier).split('.')[0],
#                         'tahun_penerbit'    : str(self.vat_supplier).split('.')[1], 
#                         'nomor_urut'        : str(self.vat_supplier).split('.')[2],
#                         'invoice_id'        : self.id,
#                         'type'              : 'in',
#                     }
#                 else:
#                     raise UserError(_('Faktur Number Wrong!\nPlease input Faktur Number use SEPARATOR "."(DOT).')) 
#                 obj_no_faktur.create(vals)
        return True
    
    
class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'
    
    default_code = fields.Char(string='SKU')
    