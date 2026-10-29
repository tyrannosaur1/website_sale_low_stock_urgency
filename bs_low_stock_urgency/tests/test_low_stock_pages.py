# -*- coding: utf-8 -*-
"""The two shop surfaces a customer meets before the cart.

Pages are fetched over HTTP and parsed: a class rendered on the wrong node,
or a badge that never reaches the markup because a template was not applied,
looks fine in the source and does nothing in a browser. The negative control
carries most of the weight -- a badge that appears everywhere would satisfy
the positive assertion alone.
"""
from lxml import html as lxml_html

from odoo.tests.common import HttpCase

from odoo.addons.bs_low_stock_urgency.tests.common import (
    storable_product_values,
)


class LowStockPagesCase(HttpCase):
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
        self.low_product = self._make_product("Scarce Page Widget", 2.0)
        self.stocked_product = self._make_product("Plenty Page Widget", 40.0)

    def _make_product(self, name, quantity):
        product = self.env["product.template"].create(dict(
            storable_product_values(),
            name=name,
            sale_ok=True,
            list_price=10.0,
            website_published=True,
            low_stock_threshold=0.0,
        ))
        self.env["stock.quant"]._update_available_quantity(
            product.product_variant_id, self.location, quantity)
        return product

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _page(self, url):
        response = self.url_open(url)
        self.assertEqual(response.status_code, 200, "page did not render: %s" % url)
        return lxml_html.fromstring(response.text)

    def _badges(self, node):
        return node.xpath(
            ".//*[contains(concat(' ', normalize-space(@class), ' '), ' o_wslsu_badge ')]")

    def _tile(self, tree, name):
        tiles = tree.xpath(
            "//*[contains(concat(' ', normalize-space(@class), ' '), ' oe_product_cart ')]")
        for tile in tiles:
            if name in tile.text_content():
                return tile
        self.fail("no shop tile rendered for %s" % name)

    def _availability_line(self, tree):
        return tree.xpath(
            "//div[contains(concat(' ', normalize-space(@class), ' '), "
            "' availability_messages ')]")

    # ------------------------------------------------------------------
    # Product page
    # ------------------------------------------------------------------
    def test_the_product_page_carries_the_badge(self):
        tree = self._page(self.low_product.website_url)
        badges = self._badges(tree)
        self.assertEqual(len(badges), 1, "the badge must be rendered exactly once")
        self.assertEqual(badges[0].text_content().strip(), "Only 2 left")
        self.assertEqual(float(badges[0].get("data-low-stock-qty")), 2.0)
        # Core's own line is still there; this module augments it.
        self.assertTrue(self._availability_line(tree))

    def test_the_product_page_leaves_a_stocked_product_alone(self):
        tree = self._page(self.stocked_product.website_url)
        self.assertTrue(self._availability_line(tree))
        self.assertEqual(self._badges(tree), [])

    def test_a_badge_that_repeats_the_core_sentence_is_not_rendered(self):
        variant = self.low_product.product_variant_id
        self.website.low_stock_badge_text = variant._low_stock_core_sentence()
        tree = self._page(self.low_product.website_url)
        self.assertEqual(self._badges(tree), [])
        self.assertTrue(self._availability_line(tree))

    # ------------------------------------------------------------------
    # Shop grid
    # ------------------------------------------------------------------
    def test_the_shop_grid_marks_only_the_low_stock_tile(self):
        tree = self._page("/shop")
        scarce_tile = self._tile(tree, "Scarce Page Widget")
        plenty_tile = self._tile(tree, "Plenty Page Widget")

        scarce_badges = self._badges(scarce_tile)
        self.assertEqual(len(scarce_badges), 1,
                         "the low-stock tile must carry one badge")
        self.assertEqual(scarce_badges[0].text_content().strip(), "Only 2 left")
        self.assertEqual(float(scarce_badges[0].get("data-low-stock-qty")), 2.0)

        self.assertEqual(self._badges(plenty_tile), [],
                         "a product above its threshold must not be marked")
