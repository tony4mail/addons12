# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError



class FakturPajakInv(models.TransientModel):
    _name = "faktur.pajak.inv"
    _description = "Faktur Pajak Invoice"

    @api.model
    def _default_get_type(self):
        return self._context.get('type', 'out_invoice')
    
    @api.model
    def _default_faktur_ids(self):
        invoice_obj = 'account.invoice'
        faktur_obj = 'nomor.faktur.pajak'
        faktur_inv_ids = (invoice_obj == self._context.get('active_model') or faktur_obj == self._context.get('active_model')) and self._context.get('active_ids') or []
        #print ('===faktur_inv_ids===',faktur_inv_ids)
        return [
            (0, 0, {'faktur_id': faktur_obj == self._context.get('active_model') and fakinv.id or False, 
                    'invoice_id': invoice_obj == self._context.get('active_model') and fakinv.id or False,
                    'company_id': faktur_obj == self._context.get('active_model') and fakinv.fp_company_id.id or \
                       invoice_obj == self._context.get('active_model') and fakinv.company_id.id or False,
                    'type_faktur': '_invoice' in fakinv.type and fakinv.type.replace("_invoice","") or fakinv.type,
                    'type_invoice': fakinv.type == 'out' and fakinv.type+'_invoice' or fakinv.type})
            for fakinv in self.env[self._context.get('active_model')].browse(faktur_inv_ids)
        ]
    
    type = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('out_refund', 'Customer Refund'),
        ('in_invoice', 'Vendor Bills'),
        ('in_refund', 'Vendor Refund')
        ], string='Type', default=_default_get_type, required=True)
    load_faktur = fields.Boolean('Load Faktur Pajak')
    faktur_invoice_ids = fields.One2many('change.invoice.faktur', 'wizard_id', string='Faktur Pajak', default=_default_faktur_ids)
#     invoice_id = fields.Many2one('account.invoice', string='Invoice')
    
    @api.model
    def default_get(self, fields):
        rec = super(FakturPajakInv, self).default_get(fields)
        active_model = self._context.get('active_model')
        active_ids = self._context.get('active_ids')
        
        # Check for selected invoices ids
        if not active_ids:
            raise UserError(_("Programming error: wizard action executed without active_ids in context."))

        fak_invoices = self.env[active_model].browse(active_ids)

        # Check all invoices are open
        if active_model == 'account.invoice' and any((invoice.state == 'cancel') for invoice in fak_invoices):
            raise UserError(_("You cannot register faktur pajak for cancelled invoices\n%s"%','.join([(invoice.display_name) for invoice in fak_invoices if invoice.nomor_faktur_id])))
        if active_model == 'account.invoice' and any((invoice.amount_tax > 0 and invoice.non_faktur_pajak) for invoice in fak_invoices):
            raise UserError(_("You can only register faktur pajak for taxed invoices and unchecked Non FP\n%s"%','.join([invoice.display_name for invoice in fak_invoices if invoice.nomor_faktur_id])))
        if active_model == 'account.invoice' and any(invoice.amount_tax == 0 for invoice in fak_invoices):
            raise UserError(_("You can only register faktur pajak for taxed invoices\n%s"%','.join([(invoice.display_name) for invoice in fak_invoices if invoice.nomor_faktur_id])))
        if active_model == 'account.invoice' and any(invoice.nomor_faktur_id for invoice in fak_invoices):
            raise UserError(_("Invoice already registered with Faktur Pajak\n%s"%','.join([(invoice.display_name) for invoice in fak_invoices if invoice.nomor_faktur_id])))
        if active_model == 'nomor.faktur.pajak' and any(faktur.state == '1' for faktur in fak_invoices):
            raise UserError(_("You can only register invoice for Unused faktur pajak\n%s"%','.join([faktur.name for faktur in fak_invoices if faktur.invoice_id])))
        return rec
    
#     @api.multi
#     def faktur_invoices(self):
#         faktur_pajaks = self.env['nomor.faktur.pajak'].browse(self._context.get('active_ids', []))
#         for faktur in faktur_pajaks:
#             faktur.invoice_id = self.invoice_id.id
#             faktur.invoice_id.non_faktur_pajak = False
#             faktur.invoice_id.nomor_faktur_id = faktur.id
#             faktur.invoice_revisi_id = False
#         return {'type': 'ir.actions.act_window_close'}

#     @api.multi
#     def get_faktur_button(self):
#         faktur_ids = self.env['nomor.faktur.pajak'].search([('type','=','out'),('state','=','0'),('invoice_id','=',False)])
#         for faktur in faktur_ids:
#             for line in self.faktur_invoice_ids:
#                 print ('---faktur_ids--',faktur_ids)
#                 line.faktur_id = faktur.id
#         return
    
    @api.onchange('load_faktur')
    def onchange_load_faktur(self):
        if not self.load_faktur:
            for iline in self.faktur_invoice_ids:
                iline.faktur_id = False
            return
        faktur_ids = self.env['nomor.faktur.pajak'].search([('type','=','out'),
            ('state','=','0'),('invoice_id','=',False),('fp_company_id','=',self.company_id.id)], limit=len(self.faktur_invoice_ids))
        for faktur in faktur_ids:
            for line in self.faktur_invoice_ids:
                line.faktur_id = faktur.id
            return
    
    @api.multi
    def change_faktur_button(self):
        self.ensure_one()
        self.faktur_invoice_ids.change_faktur_button()
        return {'type': 'ir.actions.act_window_close'}

    
class ChangeInvoiceFaktur(models.TransientModel):
    """ A model to configure users in the change password wizard. """
    _name = 'change.invoice.faktur'
    _description = 'Change Password Wizard User'
    
    @api.model
    def _default_get_type(self):
        return self._context.get('type', 'out_invoice')
    
    wizard_id = fields.Many2one('faktur.pajak.inv', string='Wizard', required=True)
    type_faktur = fields.Selection([('in','Faktur Pajak Masukan'),
        ('out','Faktur Pajak Keluaran')], string='Type', required=False)
    type_invoice = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('out_refund', 'Customer Refund'),
        ('in_invoice', 'Vendor Bills'),
        ('in_refund', 'Vendor Refund')
        ], string='Type', required=False)
    company_id = fields.Many2one('res.company', string='Company', required=False)
    faktur_id = fields.Many2one('nomor.faktur.pajak', string='Faktur Pajak', required=False, ondelete='cascade')
    invoice_id = fields.Many2one('account.invoice', string='Invoices', required=False)
 
    @api.multi
    def change_faktur_button(self):
        for line in self:
            if not line.invoice_id:
                raise UserError(_("Before clicking on Set Faktur Invoice, you have to add invoices."))
            line.invoice_id.nomor_faktur_id = line.faktur_id.id
            line.faktur_id.invoice_id = line.invoice_id.id
            line.faktur_id.invoice_revisi_id = False
            line.faktur_id.invoice_id.non_faktur_pajak = False


# class InvoiceFakturPajak(models.TransientModel):
#     _name = "invoice.faktur.pajak"
#     _description = "Faktur Pajak Invoice"
# 
#     @api.model
#     def _default_get_type(self):
#         if self._context.get('type', 'out_invoice') == 'out_invoice':
#             return 'out'
#         else:
#             return 'in'
# 
#     type = fields.Selection([('in','Faktur Pajak Masukan'),('out','Faktur Pajak Keluaran')], string='Type', default=_default_get_type, required=True)
#     nomor_faktur_id = fields.Many2one('nomor.faktur.pajak', string='Faktur Pajak')
#     
#     @api.multi
#     def invoice_faktur(self):
#         invoices = self.env['account.invoice'].browse(self._context.get('active_ids', []))
#         for inv in invoices:
#             inv.nomor_faktur_id = self.nomor_faktur_id.id
#             inv.nomor_faktur_id.invoice_id = inv.id
#         return {'type': 'ir.actions.act_window_close'}

# class ChangePasswordWizard(models.TransientModel):
#     """ A wizard to manage the change of users' passwords. """
#     _name = "change.password.wizard"
#     _description = "Change Password Wizard"
# 
#     def _default_user_ids(self):
#         user_ids = self._context.get('active_model') == 'res.users' and self._context.get('active_ids') or []
#         return [
#             (0, 0, {'user_id': user.id, 'user_login': user.login})
#             for user in self.env['res.users'].browse(user_ids)
#         ]
# 
#     user_ids = fields.One2many('change.password.user', 'wizard_id', string='Users', default=_default_user_ids)
# 
#     @api.multi
#     def change_password_button(self):
#         self.ensure_one()
#         self.user_ids.change_password_button()
#         if self.env.user in self.mapped('user_ids.user_id'):
#             return {'type': 'ir.actions.client', 'tag': 'reload'}
#         return {'type': 'ir.actions.act_window_close'}
# 
# 
# class ChangePasswordUser(models.TransientModel):
#     """ A model to configure users in the change password wizard. """
#     _name = 'change.password.user'
#     _description = 'Change Password Wizard User'
# 
#     wizard_id = fields.Many2one('change.password.wizard', string='Wizard', required=True)
#     user_id = fields.Many2one('res.users', string='User', required=True, ondelete='cascade')
#     user_login = fields.Char(string='User Login', readonly=True)
#     new_passwd = fields.Char(string='New Password', default='')
# 
#     @api.multi
#     def change_password_button(self):
#         for line in self:
#             if not line.new_passwd:
#                 raise UserError(_("Before clicking on 'Change Password', you have to write a new password."))
#             line.user_id.write({'password': line.new_passwd})
#         # don't keep temporary passwords in the database longer than necessary
#         self.write({'new_passwd': False})
