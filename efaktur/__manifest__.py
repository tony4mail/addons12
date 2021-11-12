{
    "name"          : "E-Faktur",
    "version"       : '12.0.3.0.1',
    'license'       : 'OPL-1',
    'summary'       : 'Efaktur Import for DJP',
    "depends"       : [
                       "account", 
                       "aos_l10n_id",
                       "aos_base_account",
                       "aos_account_discount",
                       #"mail_attach_existing_attachment"
    ],
    'images'        :  ['images/main_screenshot.png'],
    "author"        : "Alphasoft",
    "description"   : """This module aim to:
                    - Create Object Nomor Faktur Pajak
                    - Add Column Customer such as: 
                        * NPWP, RT, RW, Kelurahan, Kecamatan, Kabupaten, Province
                    - Just Import the file csv at directory data
                    - Export file csv for upload to efaktur""",
    "website"       : "https://www.alphasoft.co.id/",
    "category"      : "Accounting",
    "data"    : [
                "security/ir.model.access.csv",
                'security/account_security.xml',
                "data/res_country_data.xml",
                "wizard/faktur_pajak_inv_view.xml",
                "views/base_view.xml",
                "views/res_partner_view.xml",
                "views/faktur_pajak_view.xml",
                "views/account_invoice_view.xml",                     
                'views/res_config_settings_views.xml',
                #"views/company_view.xml",
                "wizard/faktur_pajak_generate.xml",
                "wizard/faktur_pajak_upload.xml",
                "wizard/fp_product_view.xml",
                "wizard/fp_partner_view.xml",
                "wizard/fp_invoice_view.xml",
    ],
    'price'         : 299.00,
    'currency'      : 'EUR',
    "init_xml"      : [],
    "demo_xml"      : [],
    'test'          : [],    
    "active"        : False,
    "installable"   : True,
    'application'   : False,
    #'post_init_hook': '_post_init',
}