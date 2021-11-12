
# try:
#     from StringIO import StringIO
# except ImportError:
#     from io import StringIO
import logging
import time

import base64, itertools, csv, codecs, io, sys

from odoo import api, fields, models, _
from odoo.modules import get_module_path
from odoo.exceptions import UserError
from .csv_reader import UnicodeWriter
            
class fp_invoice_export(models.TransientModel):
    _name = 'fp.invoice.export'
    _description = 'Export E-Faktur Invoice'
    
    type = fields.Selection([('in_invoice','Supplier Invoice'),
                             ('out_invoice','Customer Invoice'),
                             ('in_refund','Supplier Refund'),
                             ('out_refund','Customer Refund')], 'Type')
    data = fields.Binary('Download', readonly=True)
    filename = fields.Char('File Name', size=32)
    
    def _amount_currency(self, amount, inv):
        cur_obj = self.env['res.currency']
        #amount = cur_obj.with_context({'date': inv.date_invoice or time.strftime('%Y-%m-%d')}).compute(amount, inv.company_id.currency_id)
        invoice_date = inv.date_invoice or fields.Date.today()
        amount = inv.currency_id._convert(amount, inv.currency_id, inv.company_id, invoice_date)
        return amount
    
    def _amount_currency_line(self, amount, line):
        #amount = 0.0
        #if line.invoice_line_tax_ids:
        if line.price_tax:
            cur_obj = self.env['res.currency']
            invoice_date = line.invoice_id.date_invoice or fields.Date.today()
            amount = line.invoice_id.currency_id._convert(amount, line.currency_id, line.company_id, invoice_date)
            #amount = cur_obj.with_context({'date': line.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}).compute(amount, line.invoice_id.company_id.currency_id.id, round=False)
        return amount
    
    @api.multi
    def action_export(self):
        #print ('contex====',self._context)
        if self._context.get('default_type') in ('out_invoice','out_refund'):
            type = 'Keluaran'
        elif self._context.get('default_type') in ('in_invoice','in_refund'):
            type = 'Masukan'
        file_data = io.StringIO()
        rows = self.get_data()
        try:
            writer = UnicodeWriter(file_data)
            writer.writerows(rows)
            file_value = file_data.getvalue()
            self.write({'data': base64.encodestring((file_value).encode()).decode(),
                        'filename': 'Faktur Pajak %s.csv'%type})
        finally:
            file_data.close()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'fp.invoice.export',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
#     'FM','KD_JENIS_TRANSAKSI','FG_PENGGANTI','NOMOR_FAKTUR','MASA_PAJAK',
#     'TAHUN_PAJAK','TANGGAL_FAKTUR','NPWP','NAMA','ALAMAT_LENGKAP','JUMLAH_DPP',
#     'JUMLAH_PPN','JUMLAH_PPNBM','IS_CREDITABLE'
    def _get_header_fk_in(self):
        return ['FM',
                'KD_JENIS_TRANSAKSI',
                'FG_PENGGANTI',
                'NOMOR_FAKTUR',
                'MASA_PAJAK',
                'TAHUN_PAJAK',
                'TANGGAL_FAKTUR',
                'NPWP',
                'NAMA',
                'ALAMAT_LENGKAP',
                'JUMLAH_DPP',
                'JUMLAH_PPN',
                'JUMLAH_PPNBM',
                'IS_CREDITABLE']
        
    def _get_header_fk(self):
        return ['FK',
                'KD_JENIS_TRANSAKSI',
                'FG_PENGGANTI',
                'NOMOR_FAKTUR',
                'MASA_PAJAK',
                'TAHUN_PAJAK',
                'TANGGAL_FAKTUR',
                'NPWP',
                'NAMA',
                'ALAMAT_LENGKAP',
                'JUMLAH_DPP',
                'JUMLAH_PPN',
                'JUMLAH_PPNBM',
                'ID_KETERANGAN_TAMBAHAN',
                'FG_UANG_MUKA',
                'UANG_MUKA_DPP',
                'UANG_MUKA_PPN',
                'UANG_MUKA_PPNBM',
                'REFERENSI']
        
    def _get_header_lt(self, headers):
        lt_ids = {
            'FK': 'LT',
            'KD_JENIS_TRANSAKSI': 'NPWP',
            'FG_PENGGANTI': 'NAMA',
            'NOMOR_FAKTUR': 'JALAN',
            'MASA_PAJAK': 'BLOK',
            'TAHUN_PAJAK': 'NOMOR',
            'TANGGAL_FAKTUR': 'RT',
            'NPWP': 'RW',
            'NAMA': 'KECAMATAN',
            'ALAMAT_LENGKAP': 'KELURAHAN',
            'JUMLAH_DPP': 'KABUPATEN',
            'JUMLAH_PPN': 'PROPINSI',
            'JUMLAH_PPNBM': 'KODE_POS',
            'ID_KETERANGAN_TAMBAHAN': 'NOMOR_TELEPON',
            'FG_UANG_MUKA': '',
            'UANG_MUKA_DPP': '',
            'UANG_MUKA_PPN': '',
            'UANG_MUKA_PPNBM': '',
            'REFERENSI': ''
        }
        rows = [lt_ids[l] for l in headers]
        return rows
    
    def _get_header_of(self, headers):
        of_ids = {
            'FK': 'OF',
            'KD_JENIS_TRANSAKSI': 'KODE_OBJEK',
            'FG_PENGGANTI': 'NAMA',
            'NOMOR_FAKTUR': 'HARGA_SATUAN',
            'MASA_PAJAK': 'JUMLAH_BARANG',
            'TAHUN_PAJAK': 'HARGA_TOTAL',
            'TANGGAL_FAKTUR': 'DISKON',
            'NPWP': 'DPP',
            'NAMA': 'PPN',
            'ALAMAT_LENGKAP': 'TARIF_PPNBM',
            'JUMLAH_DPP': 'PPNBM',
            'JUMLAH_PPN': '',
            'JUMLAH_PPNBM': '',
            'ID_KETERANGAN_TAMBAHAN': '',
            'FG_UANG_MUKA': '',
            'UANG_MUKA_DPP': '',
            'UANG_MUKA_PPN': '',
            'UANG_MUKA_PPNBM': '',
            'REFERENSI': ''
        }
        rows = [of_ids[o] for o in headers]
        return rows
    
    def _get_invoice_line(self, headers):
        context = dict(self._context or {})
        Invoice = self.env['account.invoice']
        invoices = Invoice.browse(context.get('active_ids'))
        rows = []
        for inv in invoices:
            if not inv.invoice_line_ids:
                raise UserError(_('Make sure your invoice has a line for Invoice! %s' % inv.origin))
            total_dpp = sum(self._amount_currency_line(line.price_subtotal, line) for line in inv.invoice_line_ids) or 0
            total_ppn = sum(self._amount_currency_line(line.price_tax, line) for line in inv.invoice_line_ids) or 0
            tot_line_dpp = sum(int(round(self._amount_currency_line(line.price_subtotal, line),0)) for line in inv.invoice_line_ids) or 0
            tot_line_ppn = sum(int(round(self._amount_currency_line(line.price_tax, line),0)) for line in inv.invoice_line_ids) or 0
            #max_line_id = max(line for line in inv.invoice_line_ids if line.invoice_line_tax_ids) or 0
            max_line_id = max(line for line in inv.invoice_line_ids if line.price_tax) or 0
            
            if inv.state in ('draft','cancel'):
                raise UserError(_('Cannot export draft/cancel Invoice! %s' % inv.origin))
            #if not inv.amount_tax:
            #    raise UserError(_('Make sure select invoice which has taxes!'))
            
            if context.get('default_type') in ('out_invoice','out_refund'):
                type = 'Keluaran'
                itype = 'Masukan'
            elif context.get('default_type') in ('in_invoice','in_refund'):
                type = 'Masukan'
                itype = 'Keluaran'
            if context.get('default_type') != inv.type:
                raise UserError(_('Cannot export FP %s Invoice %s as it on FP %s.!' % (itype, inv.number, type)))
            
            
            amount_untaxed = int(round(total_dpp,0))
            amount_tax = int(round(total_ppn,0))
            residual_dpp = amount_untaxed - tot_line_dpp
            residual_ppn = amount_tax - tot_line_ppn
            if context.get('default_type') in ('out_invoice','out_refund'):
                inv_ids = {
                    'FK': 'FK',
                    'KD_JENIS_TRANSAKSI': inv.nomor_faktur_id and str(inv.nomor_faktur_id.kode_perusahaan) or '',
                    'FG_PENGGANTI': inv.nomor_faktur_id and str(inv.nomor_faktur_id.jenis_faktur) or '',
                    'NOMOR_FAKTUR': inv.nomor_faktur_id and str(inv.nomor_faktur_id.number) or '',
                    'MASA_PAJAK': int(time.strftime('%m', time.strptime(str(inv.date_invoice),'%Y-%m-%d'))),
                    'TAHUN_PAJAK': time.strftime('%Y', time.strptime(str(inv.date_invoice),'%Y-%m-%d')),
                    'TANGGAL_FAKTUR': time.strftime('%d/%m/%Y', time.strptime(str(inv.date_invoice),'%Y-%m-%d')),
                    'NPWP': inv.npwp_efaktur or '000000000000000',
                    'NAMA': inv.partner_id._get_name_npwp() or '',
                    'ALAMAT_LENGKAP': inv.partner_id._get_street_npwp() or '',
                    'JUMLAH_DPP': amount_untaxed or 0,
                    'JUMLAH_PPN': amount_tax or 0,
                    'JUMLAH_PPNBM': 0,
                    'ID_KETERANGAN_TAMBAHAN': '',
                    'FG_UANG_MUKA': 0,
                    'UANG_MUKA_DPP': 0,
                    'UANG_MUKA_PPN': 0,
                    'UANG_MUKA_PPNBM': 0,
                    'REFERENSI': inv.number or inv.origin or ''
                }
            elif context.get('default_type') in ('in_invoice','in_refund'):
                inv_ids = {
                    'FM': 'FM',
                    'KD_JENIS_TRANSAKSI': '01',
                    'FG_PENGGANTI': '0',
                    'NOMOR_FAKTUR': inv.nomor_faktur_id and inv.nomor_faktur_id.number or '',
                    'MASA_PAJAK': int(time.strftime('%m', time.strptime(str(inv.date_invoice),'%Y-%m-%d'))),
                    'TAHUN_PAJAK': time.strftime('%Y', time.strptime(str(inv.date_invoice),'%Y-%m-%d')),
                    'TANGGAL_FAKTUR': time.strftime('%d/%m/%Y', time.strptime(str(inv.date_invoice),'%Y-%m-%d')),
                    'NPWP': inv.npwp_efaktur or '000000000000000',
                    'NAMA': inv.partner_id._get_name_npwp() or '',
                    'ALAMAT_LENGKAP': inv.partner_id._get_street_npwp() or '',
                    'JUMLAH_DPP': amount_untaxed or 0,
                    'JUMLAH_PPN': amount_tax or 0,
                    'JUMLAH_PPNBM': 0,
                    'IS_CREDITABLE': '1',
                }
            row = [inv_ids[i] for i in headers]
            rows.append(list(row))
            
            if context.get('default_type') in ('out_invoice','out_refund'):
                for line in inv.invoice_line_ids:
                    #if line.invoice_line_tax_ids:
                    if line.price_tax:
                        line_dpp = int(round(self._amount_currency_line(line.price_subtotal, line),0))
                        #line_ppn = line.invoice_line_tax_ids and int(round(self._amount_currency_line(line.price_tax, line),0))
                        line_ppn = line.price_tax and int(round(self._amount_currency_line(line.price_tax, line),0))
                        if inv.company_id.discount_efaktur_display == 'no':
                            HARGA_SATUAN = int(self._amount_currency_line(line.price_subtotal/line.quantity, line)) or '0'
                            JUMLAH_BARANG = line.quantity or 1
                            HARGA_TOTAL = int(self._amount_currency_line(line.price_subtotal, line)) or '0'
                            DISKON = '0'
                            DPP = max_line_id == line and line_dpp + residual_dpp or line_dpp or '0'#line_dpp or '0'
                            PPN = max_line_id == line and line_ppn + residual_ppn or line_ppn or '0'#line_ppn or '0'
                        else:
                            HARGA_SATUAN = int(round(self._amount_currency_line(line.price_unit_undiscount_untaxed, line),0)) or '0'
                            JUMLAH_BARANG = line.quantity or 1
                            HARGA_TOTAL = int(self._amount_currency_line(line.price_undiscount_untaxed, line)) or '0'
                            DISKON = int(line.price_discount_untaxed) or '0'
                            DPP = max_line_id == line and line_dpp + residual_dpp or line_dpp or '0'
                            PPN = max_line_id == line and line_ppn + residual_ppn or line_ppn or '0'
                        #print ('=====',DPP,PPN,line_ppn,residual_ppn,max_line_id == line,line_ppn + residual_ppn)
                        #tax_amt_type = sum(tax.amount_type == 'percent' and tax.amount/100.0 or tax.amount for tax in line.invoice_line_tax_ids)
                        tax_amt_type = sum(tax.amount_type == 'percent' and tax.amount/100.0 or tax.amount for tax in line.invoice_line_tax_ids)
                        line_ids = {
                            'FK': 'OF',
                            'KD_JENIS_TRANSAKSI': line.default_code or '',
                            'FG_PENGGANTI': line.name or '',
                            'NOMOR_FAKTUR': HARGA_SATUAN,
                            'MASA_PAJAK': JUMLAH_BARANG,
                            'TAHUN_PAJAK': HARGA_TOTAL,
                            'TANGGAL_FAKTUR': DISKON,
                            'NPWP': DPP,
                            'NAMA': PPN,                 
                            'ALAMAT_LENGKAP': '0',
                            'JUMLAH_DPP': '0',
                            'JUMLAH_PPN': '',
                            'JUMLAH_PPNBM': '',
                            'ID_KETERANGAN_TAMBAHAN': '',
                            'FG_UANG_MUKA': '',
                            'UANG_MUKA_DPP': '',
                            'UANG_MUKA_PPN': '',
                            'UANG_MUKA_PPNBM': '',
                            'REFERENSI': ''
                        }
                        #print ('==D===',DPP,PPN)
                        #csvwriter.writerow([line_ids[l] for l in headers])
                        row = [line_ids[l] for l in headers]
                        rows.append(list(row))
        #print ("invoice_rows",rows)
        return rows
    
    def get_data(self, context=None):
        context = dict(self._context or {})
        if context.get('default_type') == 'out_invoice':
            get_fk_func = getattr(self, ("_get_header_fk"), None)
            get_lt_func = getattr(self, ("_get_header_lt"), None)
            get_of_func = getattr(self, ("_get_header_of"), None)
            get_inv_line_func = getattr(self, ("_get_invoice_line"), None)
            head_fk = get_fk_func()
            head_lt = get_lt_func(head_fk)
            head_of = get_of_func(head_fk)
            inv_line = get_inv_line_func(head_fk)
            rows = itertools.chain(
                                   (head_fk,),
                                   (head_lt,),
                                   (head_of,),
                                   inv_line
                                   )
        elif context.get('default_type') == 'in_invoice':
            get_fk_func = getattr(self, ("_get_header_fk_in"), None)
            get_inv_line_func = getattr(self, ("_get_invoice_line"), None)
            head_fk = get_fk_func()
            inv_line = get_inv_line_func(head_fk)
            rows = itertools.chain(
                                   (head_fk,),
                                   inv_line
                                   )
        return rows

