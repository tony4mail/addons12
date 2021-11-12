# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.modules import get_module_resource
from odoo.osv.expression import get_unaccent_wrapper
from odoo.exceptions import UserError, ValidationError
from odoo.osv.orm import browse_record

class ResCompany(models.Model):
    _inherit = "res.company"
    
    npwp = fields.Char('NPWP', compute='_compute_address', inverse='_inverse_npwp', default='00.000.000.0-000.000')
    code_transaction = fields.Selection([('01','01 Normal'),
                                         ('02','02 Bendaharawan (Tdk Terlampir)'),
                                         ('03','03 Bendaharawan (Terlampir)'),
                                         ('07','07 Batam'),
                                         ('08','08 Tanpa PPN')], compute='_compute_address', inverse='_inverse_code_transc', string='Kode Transaksi')
    blok = fields.Char('Blok', size=8, compute='_compute_address', inverse='_inverse_blok')
    nomor = fields.Char('Nomor', size=8, compute='_compute_address', inverse='_inverse_nomor')
    rt = fields.Char('RT', size=3, compute='_compute_address', inverse='_inverse_rt')
    rw = fields.Char('RW', size=3, compute='_compute_address', inverse='_inverse_rw')
    kelurahan_id = fields.Many2one('res.kelurahan', string="Kelurahan", compute='_compute_address', inverse='_inverse_kelurahan_id')
    kecamatan_id = fields.Many2one('res.kecamatan', string="Kecamatan", compute='_compute_address', inverse='_inverse_kecamatan_id')
    kabupaten_id = fields.Many2one('res.kabupaten', string="Kabupaten", compute='_compute_address', inverse='_inverse_kabupaten_id')
    #user_notif_ids = fields.Many2many('res.users', string='User Follower', required=False)
    #channel_id = fields.Many2one('mail.channel', string='Channel Follower', required=False)
    
    def _compute_address(self):
        for company in self.filtered(lambda company: company.partner_id):
            address_data = company.partner_id.sudo().address_get(adr_pref=['contact','npwp'])
            if address_data['npwp'] or company.partner_id.is_npwp:
                partner = company.partner_id.browse(address_data['npwp']).sudo()
                company.npwp = partner.npwp
                company.code_transaction = partner.code_transaction
            if address_data['contact']:
                partner = company.partner_id.browse(address_data['contact']).sudo()
                company.street = partner.street
                company.street2 = partner.street2
                company.blok = partner.blok
                company.nomor = partner.nomor
                company.rt = partner.rt
                company.rw = partner.rw
                company.kelurahan_id = partner.kelurahan_id
                company.kecamatan_id = partner.kecamatan_id
                company.kabupaten_id = partner.kabupaten_id
                company.state_id = partner.state_id
                company.city = partner.city
                company.zip = partner.zip
                company.state_id = partner.state_id
                company.country_id = partner.country_id
                #company.fax = partner.fax
                
    def _inverse_npwp(self):
        for company in self:
            company.partner_id.npwp = company.npwp
                
    def _inverse_code_transc(self):
        for company in self:
            company.partner_id.code_transaction = company.code_transaction
                
    def _inverse_blok(self):
        for company in self:
            company.partner_id.blok = company.blok
            
    def _inverse_nomor(self):
        for company in self:
            company.partner_id.nomor = company.nomor
            
    def _inverse_rt(self):
        for company in self:
            company.partner_id.rt = company.rt
            
    def _inverse_rw(self):
        for company in self:
            company.partner_id.rw = company.rw
            
    def _inverse_kelurahan_id(self):
        for company in self:
            company.partner_id.kelurahan_id = company.kelurahan_id
            
    def _inverse_kecamatan_id(self):
        for company in self:
            company.partner_id.kecamatan_id = company.kecamatan_id
            
    def _inverse_kabupaten_id(self):
        for company in self:
            company.partner_id.kabupaten_id = company.kabupaten_id
            
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
