# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models

class ResCompany(models.Model):
    _inherit = "res.company"
    
    discount_efaktur_display = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
        ], default='no', string='Display discount on efaktur')
    efaktur_automatic = fields.Boolean('Automatic efaktur')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    discount_efaktur_display = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
        ], related='company_id.discount_efaktur_display', string='Display discount on efaktur', readonly=False)    
    efaktur_automatic = fields.Boolean('Automatic efaktur', related='company_id.efaktur_automatic')
    