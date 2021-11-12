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


import itertools
from lxml import etree

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp

class NomorFakturPajak(models.Model):
    _name = "nomor.faktur.pajak"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Nomor faktur Pajak'
    
    @api.one
    @api.depends('name', 'kode_perusahaan', 'jenis_faktur', 'nomor_perusahaan', 'tahun_penerbit', 'nomor_urut', 'invoice_id', 'invoice_id.state',
                 'invoice_revisi_id', 'invoice_revisi_id.state')
    def _get_nomor_faktur(self):
        for faktur in self:    
            #faktur.name = "%s.%s.%s" % (faktur.nomor_perusahaan, faktur.tahun_penerbit, faktur.nomor_urut)
            faktur.number = "%s%s%s" % (faktur.nomor_perusahaan, faktur.tahun_penerbit, faktur.nomor_urut)
            faktur.state = '0'
            if faktur.invoice_id and faktur.invoice_id.state not in ('draft','cancel'):
                faktur.state = '1'
            elif faktur.invoice_revisi_id and faktur.invoice_revisi_id.state not in ('draft','cancel'):
                faktur.state = '2'
                
    
    kode_perusahaan = fields.Char('Kode Perusahaan', size=2)
    jenis_faktur = fields.Selection([('0','Baru'),('1','Pengganti')], string='Jenis Faktur', default='0')
    nomor_perusahaan = fields.Char('Nomor Perusahaan', size=3)
    tahun_penerbit = fields.Char('Tahun Penerbit', size=2)
    nomor_urut = fields.Char('Nomor Urut', size=8)
    name = fields.Char(string='Nomor Faktur')#, compute='_get_nomor_faktur', store=True)
    number = fields.Char(string='Nomor eFaktur', compute='_get_nomor_faktur', store=True)
    invoice_id = fields.Many2one('account.invoice', 'Invoice No', readonly=True)
    invoice_revisi_id = fields.Many2one('account.invoice', string='Revision Invoice', readonly=True)
    partner_revisi_id = fields.Many2one('res.partner', string='Revision Partner', related='invoice_revisi_id.partner_id', store=True)
    partner_id = fields.Many2one('res.partner', string='Partner', related='invoice_id.partner_id', store=True)
    amount_untaxed = fields.Monetary(string='Untaxed Amount', related='invoice_id.amount_untaxed', store=True)
    amount_tax = fields.Monetary(string='Tax Amount', related='invoice_id.amount_tax', store=True)
    date_invoice = fields.Date(string='Date Used', related='invoice_id.date_invoice', store=True)
    company_id = fields.Many2one('res.company', string='Company', related='invoice_id.company_id', store=True)
    fp_company_id = fields.Many2one('res.company', string='Faktur Company', required=True, default=lambda self: self.env['res.company']._company_default_get('nomor.faktur.pajak'))
    currency_id = fields.Many2one('res.currency', string='Currency', related='invoice_id.currency_id', store=True)
    type = fields.Selection([('in','Faktur Pajak Masukan'),('out','Faktur Pajak Keluaran')], default=lambda self: self._context.get('type', 'out'), string='Type')
    state = fields.Selection([('0','Not Used'),('1','Used'),('2','Hold')],string='Status', compute='_get_nomor_faktur', store=True)
    
    _sql_constraints = [
        ('faktur_unique', 'unique(kode_perusahaan,jenis_faktur,nomor_perusahaan,tahun_penerbit,nomor_urut,fp_company_id)', 'Number Faktur Must Be Unique per Company.'),
    ]
    
    @api.model
    def create(self, vals):
        #010.006-19.16390045        
        line = super(NomorFakturPajak, self).create(vals)
        if vals.get('name') and len(vals.get('name')) == 19:
            faktur_pajak = vals.get('name').split('.')
            faktur_pajak0 = faktur_pajak[0]
            faktur_pajak1 = faktur_pajak[0][-1]
            faktur_pajak2 = faktur_pajak[1].split('-')
            faktur_pajak3 = faktur_pajak[2]
            #print ('---faktur_pajak---',faktur_pajak1[0], faktur_pajak1[1],faktur_pajak2[0])
            line.kode_perusahaan = faktur_pajak0
            line.jenis_faktur = faktur_pajak1
            line.nomor_perusahaan = faktur_pajak2[0]
            line.tahun_penerbit = faktur_pajak2[1]
            line.nomor_urut = faktur_pajak3
        return line
    
    @api.multi
    def unlink(self):
        for faktur in self:
            if faktur.state in ('1', '2'):
                raise UserError(_('You cannot delete a faktur pajak which is Used or Hold.'))
        return super(NomorFakturPajak, self).unlink()
    
    @api.multi
    def action_reset(self):
        for faktur in self:
            faktur.invoice_id.nomor_faktur_id = False
            faktur.invoice_id = False
            faktur.invoice_revisi_id = False
    
    @api.multi
    def action_hold(self):
        for faktur in self:
            faktur.invoice_revisi_id = faktur.invoice_id and faktur.invoice_id.id or False
            faktur.invoice_id.nomor_faktur_id = False
            faktur.invoice_id = False
            
#     @api.multi
#     def write(self, vals):
#         if vals.get('invoice_id', False):
#             invoice = self.env['account.invoice'].browse(vals['invoice_id'])
#             invoice.write({'nomor_faktur_id': self.id})
#         return super(NomorFakturPajak, self).write(vals)