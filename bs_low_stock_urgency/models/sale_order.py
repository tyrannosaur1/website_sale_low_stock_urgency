# -*- coding: utf-8 -*-
from odoo import models

from .low_stock import empty_badge


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _low_stock_badge_values(self):
        """The badge for this line, read from *this line's* variant.

        The cart can hold two variants of the same product with very
        different stock -- one size nearly gone, the other plentiful. Asking
        the template would give both lines the same answer, so the line
        asks its own ``product_id``.
        """
        self.ensure_one()
        if not self.product_id:
            return empty_badge()
        return self.product_id._low_stock_badge_values()
