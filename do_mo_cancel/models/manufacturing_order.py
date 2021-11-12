from odoo import api, fields, models,exceptions
from odoo.tools.float_utils import float_round, float_compare, float_is_zero
from odoo.addons.mrp.models.mrp_workorder import MrpWorkorder


class Mrp_Workorder(models.Model):
    _inherit = 'mrp.workorder'

   
    @api.multi
    def write(self, values):
        return super(MrpWorkorder, self).write(values)

    MrpWorkorder.write = write

class Stock_Move(models.Model):
    _inherit = 'stock.move'

    def _action_cancel(self):
        quant_obj = self.env['stock.quant']
        account_move_obj = self.env['account.move']
        if self._context.get('mrp_flag', False):
            for move in self:
                if move.state == 'cancel':
                    continue
                if move.state == "done" and move.product_id.type == "product":
                    for move_line in move.move_line_ids:
                        quantity = move_line.product_uom_id._compute_quantity(move_line.qty_done, move_line.product_id.uom_id)
                        quant_obj._update_available_quantity(move_line.product_id, move_line.location_id, quantity,move_line.lot_id)
                        quant_obj._update_available_quantity(move_line.product_id, move_line.location_dest_id, quantity * -1,move_line.lot_id)
                if move.procure_method == 'make_to_order' and not move.move_orig_ids:
                    move.state = 'waiting'
                elif move.move_orig_ids and not all(orig.state in ('done', 'cancel') for orig in move.move_orig_ids):
                    move.state = 'waiting'
                else:
                    move.state = 'confirmed'
                siblings_states = (move.move_dest_ids.mapped('move_orig_ids') - move).mapped('state')
                if move.propagate:
                    if all(state == 'cancel' for state in siblings_states):
                        move.move_dest_ids.with_context({'mrp_flag':'cancel'})._action_cancel()
                else:
                    if all(state in ('done', 'cancel') for state in siblings_states):
                        move.move_dest_ids.with_context({'mrp_flag':'cancel'}).write({'procure_method': 'make_to_stock'})
                    move.move_dest_ids.write({'move_orig_ids': [(3, move.id, 0)]})
                move.with_context({'mrp_flag':'cancel'}).write({'state': 'cancel', 'move_orig_ids': [(5, 0, 0)]})
                account_moves = account_move_obj.search([('stock_move_id', '=', move.id)])
                if account_moves:
                    for account_move in account_moves:
                        account_move.quantity_done = 0.0
                        account_move.button_cancel()
                        account_move.unlink()
                return super(Stock_Move, self)._action_cancel()
        else:
            return super(Stock_Move, self)._action_cancel()


class ManufacturingOrder(models.Model):
    _inherit = "mrp.production"

    @api.multi
    def action_cancel(self):
        quant_obj = self.env['stock.quant']
        account_move_obj = self.env['account.move']
        stk_mv_obj = self.env['stock.move']
        for order in self:
            
            if self.env.user.has_group('do_mo_cancel.group_cancel_manufacturing_order'):
                moves = stk_mv_obj.search(['|',('production_id', '=', order.id),('raw_material_production_id','=',order.id)])

                for move in moves:
                    if move.state == 'cancel':
                        continue
                    if move.state == "done" and move.product_id.type == "product":
                        for move_line in move.move_line_ids:
                            quantity = move_line.product_uom_id._compute_quantity(move_line.qty_done, move_line.product_id.uom_id)
                            quant_obj._update_available_quantity(move_line.product_id, move_line.location_id, quantity,move_line.lot_id)
                            quant_obj._update_available_quantity(move_line.product_id, move_line.location_dest_id, quantity * -1,move_line.lot_id)
                    if move.procure_method == 'make_to_order' and not move.move_orig_ids:
                        move.state = 'waiting'
                    elif move.move_orig_ids and not all(orig.state in ('done', 'cancel') for orig in move.move_orig_ids):
                        move.state = 'waiting'
                    else:
                        move.state = 'confirmed'
                    siblings_states = (move.move_dest_ids.mapped('move_orig_ids') - move).mapped('state')
                    if move.propagate:
                        # only cancel the next move if all my siblings are also cancelled
                        if all(state == 'cancel' for state in siblings_states):
                            move.move_dest_ids.with_context({'mrp_flag':'cancel'})._action_cancel()
                    else:
                        if all(state in ('done', 'cancel') for state in siblings_states):
                            move.move_dest_ids.with_context({'mrp_flag':'cancel'}).write({'procure_method': 'make_to_stock'})
                        move.move_dest_ids.write({'move_orig_ids': [(3, move.id, 0)]})
                    move.with_context({'mrp_flag':'cancel'}).write({'state': 'cancel', 'move_orig_ids': [(5, 0, 0)] })#,  'move_line_ids': [(5, 0, 0)]})
                    account_moves = account_move_obj.search([('stock_move_id', '=', move.id)])

                    if account_moves:
                        for account_move in account_moves:
                            account_move.quantity_done = 0.0
                            account_move.button_cancel()
                            account_move.unlink()

                order.workorder_ids.action_cancel()

        res = super(ManufacturingOrder, self).action_cancel()
        return res