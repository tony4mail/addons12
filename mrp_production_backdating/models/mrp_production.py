# Copyright 2021 OpenSynergy Indonesia
# Copyright 2021 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models, fields


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    backdate = fields.Datetime(
        string="Backdate",
    )

    @api.multi
    def post_inventory(self):
        _super = super(MrpProduction, self)
        for document in self:
            document.move_raw_ids.write({"date_backdating": self.backdate})
            document.move_finished_ids.write({"date_backdating": self.backdate})

        res = _super.post_inventory()
        return res
