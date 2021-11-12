import logging
import time
import csv

from odoo import api, fields, models, _
from odoo.modules import get_module_path
from odoo.exceptions import UserError


class fp_product_export(models.TransientModel):
    _name = 'fp.product.export'
    _description = 'Export E-Faktur Product'

    @api.multi
    def action_export(self):
        context = dict(self._context or {})
        cr = self.env.cr
        headers = ['OB','KODE_OBJEK','NAMA','HARGA_SATUAN']

        mpath = get_module_path('efaktur')

        csvfile = open(mpath + '/static/export/fp_product.csv', 'wt')
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow([h.upper() for h in headers])

        products = self.env['product.product'].browse(context.get('active_ids'))
        i=0
        for prod in products:
            data = {
                'OB'        : 'OB',
                'KODE_OBJEK': prod.default_code or '',
                'NAMA'      : prod.name,
                'HARGA_SATUAN':prod.list_price
            }
            csvwriter.writerow([data[v] for v in headers])
            prod.fp_export=True
            prod.fp_date=time.strftime("%Y-%m-%d %H:%M:%S")
            i+=1

        cr.commit()
        csvfile.close()

        raise UserError("Export %s record(s) Done!" % i)
