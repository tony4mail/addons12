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


from odoo import api, fields, models, tools, _
from odoo.modules import get_module_resource
from odoo.osv.expression import get_unaccent_wrapper
from odoo.exceptions import UserError, ValidationError
from odoo.osv.orm import browse_record

ADDRESS_FIELDS = ('street', 'street2', 'rt', 'rw', 'kelurahan_id', 'kecamatan_id', 'kabupaten_id', 'zip', 'city', 'state_id', 'country_id')

class res_partner(models.Model):
    _inherit = 'res.partner'
    _description = 'res partner'
    
    
    @api.one
    def _get_npwp_info(self):
        partner_address = ''
        if self.is_npwp:
            partner_address = self
        elif self.child_ids:
            addr_npwp = ''
            addr_npwp = self.child_ids.filtered(lambda a: a.type == 'npwp')
            if addr_npwp:
                partner_address = addr_npwp or ''
            #===================================================================
            # GET KTP WHEN NO NPWP JUST IN CASE
            #===================================================================
            # if not partner_address and self.ktp and (partner_id.npwp == '00.000.000.0-000.000' or self.npwp == '0'):
            #     partner_address = self.ktp
            #===================================================================
        if partner_address and partner_address.npwp:
            self.npwp_no = partner_address.npwp.upper()
        if partner_address and partner_address.street:
            self.npwp_street = partner_address.street.upper()
        self.main_street = self.street
    
    fp_export = fields.Boolean(string="LT Is Exported")
    fp_date = fields.Datetime(string="LT Exported Date", required=False)
    is_npwp = fields.Boolean('Is NPWP Address?')
    npwp = fields.Char('NPWP', default='00.000.000.0-000.000', help='Nomor Pokok Wajib Pajak')
    npwp_no = fields.Char(string='No NPWP', compute='_get_npwp_info', store=False)
    npwp_street = fields.Char(string='NPWP Street', compute='_get_npwp_info', store=False)
    main_street = fields.Char(string='Main Street', compute='_get_npwp_info', store=False)
    ktp = fields.Char('ID Number')
    type = fields.Selection(selection_add=[
                             ('npwp', 'NPWP'),
                             ('ktp', 'KTP'),
                             ('technical', 'Technical')])
    cluster = fields.Selection([('yes','YES'),('no','NO')], string='Cluster', help='Cluster') 
    code_transaction = fields.Selection([('01','01 Normal'),
                                         ('02','02 Bendaharawan (Tdk Terlampir)'),
                                         ('03','03 Bendaharawan (Terlampir)'),
                                         ('07','07 Batam'),
                                         ('08','08 Tanpa PPN')], string='Kode Transaksi', 
                                        default='01', help='Kode Transaksi Faktur Pajak')
    blok = fields.Char('Blok', size=8)
    nomor = fields.Char('Nomor', size=8)
    rt = fields.Char('RT', size=3)
    rw = fields.Char('RW', size=3)
    kelurahan_id = fields.Many2one('res.kelurahan', string="Kelurahan")
    kecamatan_id = fields.Many2one('res.kecamatan', string="Kecamatan")
    kabupaten_id = fields.Many2one('res.kabupaten', string="Kabupaten")
#     state = fields.Selection([('draft','Draft'),('confirm','Confirm')], string='Status') 
    
#     _sql_constraints = [
#         ('npwp_uniq', 'unique(npwp)', 'The npwp of the customer must be unique!'),
#     ]
    
#     @api.multi
#     def _display_address(self, without_company=False):
# 
#         '''
#         The purpose of this function is to build and return an address formatted accordingly to the
#         standards of the country where it belongs.
# 
#         :param address: browse record of the res.partner to format
#         :returns: the address formatted in a display that fit its country habits (or the default ones
#             if not country is specified)
#         :rtype: string
#         '''
#         # get the information that will be injected into the display format
#         # get the address format
#         address_format = self.country_id.address_format or \
#               "%(street)s\n%(street2)s Blok %(blok)s/No.%(nomor)s RT/RW: %(rt)s/%(rw)s\nKel. %(kelurahan_name)s, Kec. %(kecamatan_name)s, Kab. %(kabupaten_name)s\n%(city)s - %(state_name)s %(zip)s\n%(country_name)s"
#         args = {
#             'state_code': self.state_id.code or '',
#             'state_name': self.state_id.name or '',
#             'country_code': self.country_id.code or '',
#             'country_name': self.country_id.name or '',
#             'company_name': self.commercial_company_name or '',
#             'blok': self.blok or '',
#             'nomor': self.nomor or '',
#             'rt': 'RT:'+ self.rt or '',
#             'rw': 'RW'+ self.rw or '',
#             'kabupaten_name': self.kabupaten_id.name or '',
#             'kecamatan_name': self.kecamatan_id.name or '',
#             'kelurahan_name': self.kelurahan_id.name or '',
#         }
#         for field in self._address_fields():
#             args[field] = getattr(self, field) or ''
#         if without_company:
#             args['company_name'] = ''
#         elif self.commercial_company_name:
#             address_format = '%(company_name)s\n' + address_format
#         return address_format % args

    
#     @api.onchange('state_id')
#     def onchange_state_id(self):
#         if not self.state_id:
#             return
#         if self.state_id:
#             self.kecamatan_id = False
#             self.kabupaten_id = False
#             self.kelurahan_id = False
#             self.city = ''
#             self.zip = ''
    
    @api.onchange('kelurahan_id')
    def onchange_kelurahan_id(self):
        if not self.kelurahan_id:
            return
        if self.kelurahan_id.kecamatan_id:
            self.kecamatan_id = self.kelurahan_id.kecamatan_id.id
        if self.kelurahan_id.kabupaten_id:
            self.kabupaten_id = self.kelurahan_id.kabupaten_id.id
            self.city = self.kelurahan_id.kabupaten_id.name
        if self.kelurahan_id.kabupaten_id and self.kelurahan_id.kabupaten_id.state_id:
            self.state_id = self.kelurahan_id.kabupaten_id.state_id.id
        if self.kelurahan_id.kabupaten_id and self.kelurahan_id.kabupaten_id.state_id and self.kelurahan_id.kabupaten_id.state_id.country_id:
            self.country_id = self.kelurahan_id.kabupaten_id.state_id.country_id.id
        if self.kelurahan_id.zip:
            self.zip = self.kelurahan_id.zip
        
    @api.onchange('kecamatan_id')
    def onchange_kecamatan_id(self):
        if not self.kecamatan_id:
            return
        if self.kecamatan_id.kabupaten_id:
            self.kabupaten_id = self.kecamatan_id.kabupaten_id.id
            self.city = self.kecamatan_id.kabupaten_id.name
        if self.kecamatan_id.kabupaten_id and self.kecamatan_id.kabupaten_id.state_id:
            self.state_id = self.kecamatan_id.kabupaten_id.state_id.id
        if self.kecamatan_id.kabupaten_id and self.kecamatan_id.kabupaten_id.state_id and self.kecamatan_id.kabupaten_id.state_id.country_id:
            self.country_id = self.kecamatan_id.kabupaten_id.state_id.country_id.id
#         if self.kecamatan_id:
#             self.kelurahan_id = False
            
    @api.onchange('kabupaten_id')
    def onchange_kabupaten_id(self):
        if not self.kabupaten_id:
            return
        if self.kabupaten_id.state_id:
            self.state_id = self.kabupaten_id.state_id.id or False
        if self.kabupaten_id.state_id and self.kabupaten_id.state_id.country_id:
            self.country_id = self.kabupaten_id.state_id.country_id.id
#         if self.kabupaten_id:
#             self.kecamatan_id = False
#             self.kelurahan_id = False
#             self.state_id = False
#             self.zip = ''
            
    @api.onchange('zip')
    def onchange_zip(self):
        if not self.zip:
            return
        kelurahan_obj = self.env['res.kelurahan']
        kelurahan_id = kelurahan_obj.search([('zip','=',self.zip)])
        if kelurahan_id:
            if len(kelurahan_id) == 1:
                kelurahan = kelurahan_id
            else:
                kelurahan = kelurahan_id[0]
            if kelurahan:
                self.kelurahan_id = kelurahan.id
            if kelurahan.kecamatan_id:
                self.kecamatan_id = kelurahan.kecamatan_id.id
            if kelurahan.kabupaten_id:
                self.kabupaten_id = kelurahan.kabupaten_id.id
                self.city = kelurahan.kabupaten_id.name
            if kelurahan.kabupaten_id and kelurahan.kabupaten_id.state_id:
                self.state_id = kelurahan.kabupaten_id.state_id.id
            if kelurahan.kabupaten_id and kelurahan.kabupaten_id.state_id and kelurahan.kabupaten_id.state_id.country_id:
                self.country_id = kelurahan.kabupaten_id.state_id.country_id.id
    
    @api.onchange('npwp')
    def onchange_npwp(self):
        res = {}
        vals = {}
        if not self.npwp:
            return
        elif len(self.npwp)==20:
            self.npwp = self.npwp
        elif len(self.npwp)==15:
            formatted_npwp = self.npwp[:2]+'.'+self.npwp[2:5]+'.'+self.npwp[5:8]+'.'+self.npwp[8:9]+'-'+self.npwp[9:12]+'.'+self.npwp[12:15]
            self.npwp = formatted_npwp
        else:
            warning = {
                'title': _('Warning'),
                'message': _('Wrong Format must 15 digit'),
            }
            return {'warning': warning, 'value' : {'npwp' : False}}
        return res
    
    
    
    @api.one
    def _get_no_npwp(self):
        partner = ''
        partner_address = self
        if self.is_npwp:
            partner_address = self
            partner = self.npwp
        elif self.child_ids:
            addr_npwp = ''
            addr_npwp = self.child_ids.filtered(lambda a: a.type == 'npwp')
            if addr_npwp:
                partner_address = addr_npwp or ''
        elif self.parent_id and self.parent_id.child_ids:
            addr_npwp = ''
            addr_npwp = self.parent_id.child_ids.filtered(lambda a: a.type == 'npwp')
            if addr_npwp:
                partner_address = addr_npwp or ''
        #print "===partner===",partner,self.is_npwp
        if not self.is_npwp and partner_address and partner_address.npwp:
            partner = partner_address.npwp
        elif not self.is_npwp and self.ktp:
            partner = self.ktp
        elif not partner:
            partner = '00.000.000.0-000.000'
        return partner.upper()
    
    def _get_name_npwp(self):
        partner = ''
        partner_address = self
        is_child = False
        if self.is_npwp:
            partner_address = self
            partner = self.name
        elif self.child_ids:
            addr_npwp = ''
            addr_npwp = self.child_ids.filtered(lambda a: a.type == 'npwp')
            if addr_npwp:
                is_child = True
                partner_address = addr_npwp or ''
        elif self.parent_id and self.parent_id.child_ids:
            addr_npwp = ''
            addr_npwp = self.parent_id.child_ids.filtered(lambda a: a.type == 'npwp')
            if addr_npwp:
                partner_address = addr_npwp or ''
        if self.is_npwp and partner_address and partner_address.name:
            partner = partner_address.name
        elif not self.is_npwp and is_child:
            partner = partner_address.name
        elif not self.is_npwp and self.ktp and not is_child:# and (self.npwp == '00.000.000.0-000.000' or self.npwp == '0'):
            partner = self.ktp+'#NIK#NAMA#'+partner_address.name
        elif not partner:
            partner = partner_address.name
        return partner.upper()
    
    def _get_street_npwp(self):
        partner = ''
        partner_address = self
        if self.is_npwp:
            partner_address = self
        elif self.child_ids:
            addr_npwp = ''
            addr_npwp = self.child_ids.filtered(lambda a: a.type == 'npwp')
            if addr_npwp:
                partner_address = addr_npwp or ''
        elif self.parent_id and self.parent_id.child_ids:
            addr_npwp = ''
            addr_npwp = self.parent_id.child_ids.filtered(lambda a: a.type == 'npwp')
            if addr_npwp:
                partner_address = addr_npwp or ''
        if partner_address.street:
            partner += ' ' +partner_address.street or ''
        if partner_address.street2:
            partner += ' ' + partner_address.street2 or ''
        if partner_address.blok:
            partner += ' ' + str(partner_address.blok) or ''
        if partner_address.nomor:
            partner += ' ' + str(partner_address.nomor) or ''
        if partner_address.rt:
            partner += ' ' + str(partner_address.rt) or ''
        if partner_address.rw:
            partner += ' ' + str(partner_address.rw) or ''
        if partner_address.blok:
            partner += ' ' + str(partner_address.blok) or ''
        if partner_address.kelurahan_id:
            partner += partner_address.kelurahan_id and ' ' +partner_address.kelurahan_id.name or ''
        if partner_address.kecamatan_id:
            partner += partner_address.kecamatan_id and ' ' +partner_address.kecamatan_id.name or ''
        if partner_address.kabupaten_id:
            partner += partner_address.kabupaten_id and ' ' +partner_address.kabupaten_id.name or ''
        if partner_address.state_id:
            partner += partner_address.state_id and ' ' +partner_address.state_id.name or ''
        if partner_address.zip:
            partner += ' ' +str(partner_address.zip) or ''
        if partner_address.blok:
            partner += ' ' +str(partner_address.phone) or ''
        return partner.upper()
    
    def _get_address_npwp(self, partner_id, type):
        address = self.env['res.partner'].browse(partner_id.id)
        partner_address = ''       
        if not address.is_npwp and address.child_ids:
            add_npwp = False
            for add_npwp in address.child_ids:
                if add_npwp.type == 'npwp':
                    address = add_npwp
            if add_npwp:
                if type == 'nama':
                    partner_address = address.name or ''
                elif type == 'npwp' and address.npwp:
                    partner_address = address.npwp
                    partner_address = partner_address.replace('.','')
                    partner_address = partner_address.replace('-','')
                elif type == 'jalan':
                    partner_address = address.street and address.street2 and address.street + ' ' + address.street2 or address.street or ''
                elif type == 'blok':
                    partner_address = address.blok or ''
                elif type == 'nomor':
                    partner_address = address.nomor or ''
                elif type == 'rt':
                    partner_address = address.rt or ''
                elif type == 'rw':
                    partner_address = address.rw or ''
                elif type == 'kel':
                    partner_address = address.kelurahan_id and address.kelurahan_id.name or ''
                elif type == 'kec':
                    partner_address = address.kecamatan_id and address.kecamatan_id.name or ''
                elif type == 'kab':
                    partner_address = address.kabupaten_id and address.kabupaten_id.name or ''
                elif type == 'prop':
                    partner_address = address.state_id and address.state_id.name or ''
                elif type == 'kode_pos':
                    partner_address = address.zip or ''
                elif type == 'no_telp':
                    partner_address = address.phone or ''
        if not partner_address and address.is_npwp:
            if type == 'nama':
                partner_address = address.name or ''
            elif type == 'npwp':
                partner_address = address.npwp
                partner_address = partner_address.replace('.','')
                partner_address = partner_address.replace('-','')
            elif type == 'jalan':
                partner_address = address.street and address.street2 and address.street + ' ' + address.street2 or address.street or ''
            elif type == 'blok':
                partner_address = address.blok or ''
            elif type == 'nomor':
                partner_address = address.nomor or ''
            elif type == 'rt':
                partner_address = address.rt or ''
            elif type == 'rw':
                partner_address = address.rw or ''
            elif type == 'kel':
                partner_address = address.kelurahan_id and address.kelurahan_id.name or ''
            elif type == 'kec':
                partner_address = address.kecamatan_id and address.kecamatan_id.name or ''
            elif type == 'kab':
                partner_address = address.kabupaten_id and address.kabupaten_id.name or ''
            elif type == 'prop':
                partner_address = address.state_id and address.state_id.name or ''
            elif type == 'kode_pos':
                partner_address = address.zip or ''
            elif type == 'no_telp':
                partner_address = address.phone or ''
        return partner_address.upper()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
