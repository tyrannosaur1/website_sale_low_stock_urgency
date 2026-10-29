# -*- coding: utf-8 -*-
"""The cart line states its own variant's quantity.

Two lines of the same product are the point of this file: one size nearly
gone, the other plentiful. An implementation that asks the template answers
"2 left" twice; the line has to ask its own ``product_id``.
"""
from lxml import html as lxml_html

from odoo.tests.common import TransactionCase

from odoo.addons.bs_low_stock_urgency.tests.common import (
    storable_product_values,
)


class LowStockCartCase(TransactionCase):
    def setUp(self):
        super().setUp()
        self.website = self.env["website"].search([], limit=1)
        self.website.write({
            "low_stock_threshold": 5,
            "low_stock_critical_threshold": 0,
            "low_stock_badge_text": "Only {qty} left",
            "low_stock_badge_critical_text": "Last few",
        })
        self.location = self.env["stock.location"].search(
            [("usage", "=", "internal")], limit=1)
        self.partner = self.env["res.partner"].create({"name": "Cart Shopper"})

        attribute = self.env["product.attribute"].create({
            "name": "Size",
            "value_ids": [(0, 0, {"name": "Small"}), (0, 0, {"name": "Large"})],
        })
        self.product = self.env["product.template"].create(dict(
            storable_product_values(),
            name="Two Size Widget",
            sale_ok=True,
            list_price=10.0,
            attribute_line_ids=[(0, 0, {
                "attribute_id": attribute.id,
                "value_ids": [(6, 0, attribute.value_ids.ids)],
            })],
        ))
        self.small, self.large = self.product.product_variant_ids.sorted("id")
        self.env["stock.quant"]._update_available_quantity(
            self.small, self.location, 2.0)
        self.env["stock.quant"]._update_available_quantity(
            self.large, self.location, 40.0)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _order(self):
        return self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "website_id": self.website.id,
            "order_line": [
                (0, 0, {"product_id": self.small.id, "product_uom_qty": 1.0}),
                (0, 0, {"product_id": self.large.id, "product_uom_qty": 1.0}),
            ],
        })

    def _badge(self, line):
        # 13.0 renders through the public `render`, not `_render`.
        renderer = self.env["ir.qweb"]
        render = getattr(renderer, "_render", None) or renderer.render
        markup = render(
            "bs_low_stock_urgency.low_stock_badge", {"badge_source": line})
        # 13.0 renders to bytes; an empty badge is b'' and would not read as
        # empty after str().
        if isinstance(markup, bytes):
            markup = markup.decode("utf-8")
        if not markup.strip():
            return None
        tree = lxml_html.fromstring(markup)
        badges = tree.xpath(
            "//*[contains(concat(' ', normalize-space(@class), ' '), ' o_wslsu_badge ')]")
        self.assertLessEqual(len(badges), 1)
        return badges[0] if badges else None

    def _line(self, order, variant):
        return order.order_line.filtered(lambda line: line.product_id == variant)

    # ------------------------------------------------------------------
    # Per-variant quantity
    # ------------------------------------------------------------------
    def test_each_cart_line_states_its_own_variant_quantity(self):
        order = self._order()
        small_line = self._line(order, self.small)
        large_line = self._line(order, self.large)

        small_badge = self._badge(small_line)
        self.assertIsNotNone(small_badge, "the scarce variant must be marked")
        self.assertEqual(small_badge.text_content().strip(), "Only 2 left")
        self.assertEqual(float(small_badge.get("data-low-stock-qty")), 2.0)

        self.assertIsNone(self._badge(large_line),
                          "the plentiful variant of the same product must not be marked")

    def test_the_badge_does_not_use_the_templates_stock(self):
        """A template-level answer would state the sum of both variants."""
        order = self._order()
        self.assertEqual(self.small.free_qty + self.large.free_qty, 42.0)
        small_badge = self._badge(self._line(order, self.small))
        self.assertEqual(small_badge.text_content().strip(), "Only 2 left")
        self.assertIsNone(self._badge(self._line(order, self.large)))

    def test_a_line_above_the_threshold_has_no_badge(self):
        self.env["stock.quant"]._update_available_quantity(
            self.small, self.location, 10.0)
        self.small.invalidate_cache()
        order = self._order()
        self.assertIsNone(self._badge(self._line(order, self.small)))

    def test_an_untracked_line_has_no_badge(self):
        service = self.env["product.product"].create({
            "name": "Service Widget",
            "type": "service",
            "sale_ok": True,
            "list_price": 10.0,
        })
        order = self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "website_id": self.website.id,
            "order_line": [(0, 0, {
                "product_id": service.id, "product_uom_qty": 1.0})],
        })
        self.assertIsNone(self._badge(order.order_line))
