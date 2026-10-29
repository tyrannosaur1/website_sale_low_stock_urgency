# -*- coding: utf-8 -*-
from odoo import models

from .low_stock import (
    DEFAULT_BADGE_TEXT,
    DEFAULT_CRITICAL_TEXT,
    core_availability_sentence,
    empty_badge,
    is_stock_tracked,
    normalize,
    render_text,
    translate,
    website_of,
)


class ProductProduct(models.Model):
    _inherit = "product.product"

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------
    def _low_stock_threshold(self):
        """A variant answers with its product's resolved threshold.

        The threshold is a product decision, not a variant one: the variants
        of a product share a shelf and a merchant sets the rule once. The
        *quantity* is read per variant, which is what the shop surfaces show.
        """
        self.ensure_one()
        return self.product_tmpl_id._low_stock_threshold()

    def _low_stock_core_sentence(self):
        """The stock sentence core prints for this variant, for comparison."""
        self.ensure_one()
        return core_availability_sentence(self.env, self, self.sudo().free_qty)

    # ------------------------------------------------------------------
    # The badge itself
    # ------------------------------------------------------------------
    def _low_stock_badge_values(self):
        """``low_stock_badge_*`` keys, filled only when a badge applies.

        Every reason not to show a badge is checked before the text is
        computed, in the order that keeps the answer cheap: untracked stock,
        no threshold, no site, quantity out of range. The quantity is
        ``free_qty`` -- the sellable number -- never ``qty_available``.

        Stock is read through a sudo record: a public visitor may see the
        product and its price but has no Inventory access, and the free
        quantity is the one stock figure the shop is allowed to summarise.
        """
        self.ensure_one()
        if not is_stock_tracked(self) or not self.sale_ok:
            return empty_badge()

        threshold = self._low_stock_threshold()
        if threshold <= 0:
            return empty_badge()

        website = website_of(self.env)
        if not website:
            return empty_badge()

        quantity = self.sudo().free_qty
        # Zero and below belong to the out-of-stock sentence core already
        # prints; "Only 0 left" is not a scarcity claim, it is a duplicate
        # of a message the customer has read one line above.
        if quantity <= 0 or quantity > threshold:
            return empty_badge()

        critical_threshold = website.low_stock_critical_threshold
        critical = bool(critical_threshold > 0 and quantity <= critical_threshold)
        if critical:
            text = website.low_stock_badge_critical_text or translate(
                self.env, DEFAULT_CRITICAL_TEXT)
        else:
            text = website.low_stock_badge_text or translate(
                self.env, DEFAULT_BADGE_TEXT)
        text = render_text(text, quantity)

        # The one duplication this module refuses to ship: a badge that says
        # exactly what core says, word for word, on the same page.
        if normalize(text) == normalize(self._low_stock_core_sentence()):
            return empty_badge()

        return {
            "low_stock_badge_text": text,
            "low_stock_badge_qty": float(quantity),
            "low_stock_badge_critical": critical,
        }
