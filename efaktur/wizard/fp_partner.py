import logging
import time
import csv

from odoo import api, fields, models, _
from odoo.modules import get_module_path
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class fp_partner_export(models.TransientModel):
    _name = 'fp.partner.export'
    _description = 'Export E-Faktur Partner'
    
    download = fields.Boolean('Download')
    
    @api.multi
    def action_export(self):
        context = dict(self._context or {})
        cr = self.env.cr
        
        headers = ['LT','NPWP','NAMA','JALAN','BLOK','NOMOR','RT','RW','KECAMATAN','KELURAHAN','KABUPATEN','PROPINSI','KODE_POS','NOMOR_TELEPON']
        mpath = get_module_path('efaktur')
        csvfile = open(mpath + '/static/export/fp_partner.csv', 'wt')
        #print "===headers===",headers
        #csvwriter = csv.writer(csvfile, delimiter=',')
        csvwriter = csv.writer(csvfile)
        #csvwriter.writerow(('Title 1', 'Title 2', 'Title 3', 'Title 4'))
        csvwriter.writerow([h.upper() for h in headers])
        Partner = self.env['res.partner']
        partners = Partner.browse(context.get('active_ids'))
        i=0
        for part in partners:
            data = {
                'LT'        : 'LT',
                'NPWP'      : Partner._get_address_npwp(part, 'npwp') or '000000000000000',
                'NAMA'      : Partner._get_address_npwp(part, 'nama') or '',#part.name or '',
                'JALAN'     : Partner._get_address_npwp(part, 'jalan') or '',#part.street or '',
                'BLOK'      : Partner._get_address_npwp(part, 'blok') or '',#part.blok or '',
                'NOMOR'     : Partner._get_address_npwp(part, 'nomor') or '',#part.nomor or '',
                'RT'        : Partner._get_address_npwp(part, 'rt') or '',#part.rt or '',
                'RW'        : Partner._get_address_npwp(part, 'rw') or '',#part.rw or '',
                'KECAMATAN' : Partner._get_address_npwp(part, 'kec') or '',#part.kecamatan_id.name or '',
                'KELURAHAN' : Partner._get_address_npwp(part, 'kel') or '',#part.kelurahan_id.name or '',
                'KABUPATEN' : Partner._get_address_npwp(part, 'kab') or '',#part.kecamatan_id.kota_id.name or '',
                'PROPINSI'  : Partner._get_address_npwp(part, 'prop') or '',#part.state_id.name or '',
                'KODE_POS'  : Partner._get_address_npwp(part, 'kode_pos') or '',#part.zip or '',
                'NOMOR_TELEPON': Partner._get_address_npwp(part, 'no_telp') or '',#part.phone or ''
            }
            
            csvwriter.writerow([data[v] for v in headers])
            part.fp_export=True
            part.fp_date=time.strftime("%Y-%m-%d %H:%M:%S")
            i+=1
        
        cr.commit()
        csvfile.close()
        raise UserError("Export %s record(s) Done!" % i)
