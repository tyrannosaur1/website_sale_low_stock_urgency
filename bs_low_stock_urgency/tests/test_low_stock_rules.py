# -*- coding: utf-8 -*-
"""Threshold resolution and the reasons a badge stays away.

These assertions are about numbers a customer reads: the badge must state
the *sellable* quantity, it must appear exactly at the threshold and not one
unit later, and it must not repeat the stock sentence that core already
prints on the same page.
"""
from odoo.tests.common import TransactionCase

from odoo.addons.bs_low_stock_urgency.models.low_stock import (
    is_stock_tracked,
    normalize,
)
from odoo.addons.bs_low_stock_urgency.tests.common import (
    storable_product_values,
    untracked_product_values,
)


class LowStockRulesCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env["website"].search([], limit=1)
        cls.website.write({
            "low_stock_threshold": 5,
            "low_stock_critical_threshold": 2,
            "low_stock_badge_text": "Only {qty} left",
            "low_stock_badge_critical_text": "Last few",
        })
        cls.location = cls.env["stock.location"].search(
            [("usage", "=", "internal")], limit=1)
        cls.category = cls.env["product.public.category"].create({
            "name": "Low Stock Test Category",
            "low_stock_threshold": 3,
        })

    # ------------------------------------------------------------------
    # Fixtures
    # ------------------------------------------------------------------
    def _product(self, name="Scarce Widget", quantity=10.0, threshold=0.0,
                 category=None, storable=True, **values):
        product_values = {
            "name": name,
            "sale_ok": True,
            "list_price": 10.0,
            "low_stock_threshold": threshold,
        }
        if storable:
            product_values.update(storable_product_values())
        else:
            product_values.update(untracked_product_values())
        if category:
            product_values["public_categ_ids"] = [(6, 0, category.ids)]
        product_values.update(values)
        product = self.env["product.template"].create(product_values)
        if quantity and storable:
            self.env["stock.quant"]._update_available_quantity(
                product.product_variant_id, self.location, quantity)
        return product

    # ------------------------------------------------------------------
    # Where the threshold comes from
    # ------------------------------------------------------------------
    def test_the_product_value_wins_over_category_and_website(self):
        product = self._product(quantity=7.0, threshold=7.0, category=self.category)
        self.assertEqual(product._low_stock_threshold(), 7.0)
        product.product_variant_id.invalidate_cache()
        self.assertEqual(product.product_variant_id._low_stock_badge_values()[
            "low_stock_badge_qty"], 7.0)

    def test_a_product_set_to_zero_inherits_its_category(self):
        product = self._product(threshold=0.0, category=self.category)
        self.assertEqual(product._low_stock_threshold(), 3.0)

    def test_a_category_set_to_zero_inherits_the_website(self):
        empty_category = self.env["product.public.category"].create({
            "name": "Inheriting Category", "low_stock_threshold": 0.0})
        product = self._product(threshold=0.0, category=empty_category)
        self.assertEqual(product._low_stock_threshold(), 5.0)

    def test_a_category_walks_to_its_parent(self):
        parent = self.env["product.public.category"].create({
            "name": "Parent Category", "low_stock_threshold": 4.0})
        child = self.env["product.public.category"].create({
            "name": "Child Category", "parent_id": parent.id,
            "low_stock_threshold": 0.0})
        product = self._product(threshold=0.0, category=child)
        self.assertEqual(product._low_stock_threshold(), 4.0)

    def test_the_nearest_category_answers_first(self):
        parent = self.env["product.public.category"].create({
            "name": "Wide Category", "low_stock_threshold": 8.0})
        child = self.env["product.public.category"].create({
            "name": "Narrow Category", "parent_id": parent.id,
            "low_stock_threshold": 2.0})
        product = self._product(threshold=0.0, category=child)
        self.assertEqual(product._low_stock_threshold(), 2.0)

    def test_zero_everywhere_turns_the_badge_off(self):
        self.website.low_stock_threshold = 0
        empty_category = self.env["product.public.category"].create({
            "name": "No Threshold Category", "low_stock_threshold": 0.0})
        product = self._product(quantity=1.0, threshold=0.0, category=empty_category)
        self.assertEqual(product._low_stock_threshold(), 0.0)
        self.assertFalse(product.product_variant_id._low_stock_badge_values()[
            "low_stock_badge_text"])

    # ------------------------------------------------------------------
    # Quantity
    # ------------------------------------------------------------------
    def test_untracked_stock_never_gets_a_badge(self):
        product = self._product(
            name="Service Widget", threshold=9.0, storable=False)
        variant = product.product_variant_id
        self.assertFalse(is_stock_tracked(variant))
        self.assertFalse(variant._low_stock_badge_values()["low_stock_badge_text"])

    def test_quantity_at_the_threshold_badges(self):
        product = self._product(quantity=5.0)
        variant = product.product_variant_id
        values = variant._low_stock_badge_values()
        self.assertEqual(values["low_stock_badge_text"], "Only 5 left")
        self.assertEqual(values["low_stock_badge_qty"], 5.0)
        self.assertFalse(values["low_stock_badge_critical"])

    def test_one_above_the_threshold_does_not(self):
        product = self._product(quantity=6.0)
        self.assertFalse(product.product_variant_id._low_stock_badge_values()[
            "low_stock_badge_text"])

    def test_zero_quantity_is_left_to_the_out_of_stock_line(self):
        product = self._product(quantity=0.0)
        self.assertFalse(product.product_variant_id._low_stock_badge_values()[
            "low_stock_badge_text"])

    def test_the_count_is_free_qty_not_on_hand(self):
        """Ten on the shelf, eight already promised: the badge says two."""
        self.website.low_stock_critical_threshold = 0
        product = self._product(quantity=10.0)
        variant = product.product_variant_id
        quant = self.env["stock.quant"].search([
            ("product_id", "=", variant.id),
            ("location_id", "=", self.location.id),
        ], limit=1)
        quant.reserved_quantity = 8.0
        variant.invalidate_cache()
        self.assertEqual(variant.qty_available, 10.0)
        self.assertEqual(variant.free_qty, 2.0)
        values = variant._low_stock_badge_values()
        self.assertEqual(values["low_stock_badge_text"], "Only 2 left")
        self.assertEqual(values["low_stock_badge_qty"], 2.0)

    # ------------------------------------------------------------------
    # Wording
    # ------------------------------------------------------------------
    def test_the_badge_text_is_configurable(self):
        self.website.low_stock_badge_text = "Hurry, {qty} left!"
        product = self._product(quantity=4.0)
        self.assertEqual(product.product_variant_id._low_stock_badge_values()[
            "low_stock_badge_text"], "Hurry, 4 left!")

    def test_a_stray_brace_does_not_break_the_badge(self):
        self.website.low_stock_badge_text = "Only {qty left"
        product = self._product(quantity=4.0)
        self.assertEqual(product.product_variant_id._low_stock_badge_values()[
            "low_stock_badge_text"], "Only {qty left")

    def test_the_urgent_text_starts_at_the_tighter_threshold(self):
        product = self._product(quantity=2.0)
        values = product.product_variant_id._low_stock_badge_values()
        self.assertTrue(values["low_stock_badge_critical"])
        self.assertEqual(values["low_stock_badge_text"], "Last few")

        other = self._product(name="Three Left Widget", quantity=3.0)
        other_values = other.product_variant_id._low_stock_badge_values()
        self.assertFalse(other_values["low_stock_badge_critical"])
        self.assertEqual(other_values["low_stock_badge_text"], "Only 3 left")

    def test_a_badge_that_repeats_the_core_sentence_is_dropped(self):
        """The one duplication this module refuses to ship."""
        self.website.low_stock_critical_threshold = 0
        product = self._product(quantity=2.0)
        variant = product.product_variant_id
        core = variant._low_stock_core_sentence()
        self.assertIn("2", core)
        self.website.low_stock_badge_text = core
        self.assertFalse(variant._low_stock_badge_values()["low_stock_badge_text"])

        # Negative control: one word different and the badge is back, so the
        # check is about the sentence, not about that quantity being hidden.
        self.website.low_stock_badge_text = core + " Order soon."
        values = variant._low_stock_badge_values()
        self.assertTrue(values["low_stock_badge_text"])
        self.assertNotEqual(normalize(values["low_stock_badge_text"]), normalize(core))
