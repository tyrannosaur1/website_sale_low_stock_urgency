# -*- coding: utf-8 -*-
from odoo import fields, models

from .low_stock import empty_badge, website_of


class ProductPublicCategory(models.Model):
    _inherit = "product.public.category"

    low_stock_threshold = fields.Float(
        "Low Stock Threshold", default=0.0, digits="Product Unit of Measure",
        help="Show the scarcity badge for products in this category when "
             "their sellable quantity is at or below this number. 0 passes "
             "the question to the parent category and then to the website.",
    )

    def _low_stock_category_threshold(self):
        """This category's threshold, or the nearest ancestor's.

        Same walk as the ordering-rules module: nearest category first, a
        non-zero value stops the walk, and a visited set keeps a corrupted
        parent loop from hanging the shop.
        """
        self.ensure_one()
        seen = self.browse()
        category = self
        while category:
            if category.low_stock_threshold > 0:
                return category.low_stock_threshold
            seen |= category
            category = category.parent_id - seen
        return 0.0


class ProductTemplate(models.Model):
    _inherit = "product.template"

    low_stock_threshold = fields.Float(
        "Low Stock Threshold", default=0.0, digits="Product Unit of Measure",
        help="Show the scarcity badge when this product's sellable quantity "
             "is at or below this number. 0 inherits the public category, "
             "which in turn inherits the website. The badge never appears "
             "for products whose stock is not tracked.",
    )

    # ------------------------------------------------------------------
    # Resolving the threshold
    # ------------------------------------------------------------------
    def _low_stock_category_threshold(self):
        """The first threshold found on the product's public categories.

        A product can sit in several categories. The lowest id wins, then
        that category's own parents -- the same tie-breaker the ordering
        rules use, so a merchant reordering categories cannot silently
        change the answer.
        """
        self.ensure_one()
        for category in self.public_categ_ids.sorted("id"):
            value = category._low_stock_category_threshold()
            if value > 0:
                return value
        return 0.0

    def _low_stock_threshold(self):
        """The number this product's badge is measured against; 0 is off.

        Product, then category (nearest ancestor first), then the website.
        A product that sets 0 is not "never badge": it is "ask my category",
        and a category that sets 0 is "ask the site".
        """
        self.ensure_one()
        if self.low_stock_threshold > 0:
            return self.low_stock_threshold
        category = self._low_stock_category_threshold()
        if category > 0:
            return category
        website = website_of(self.env)
        return website.low_stock_threshold if website else 0.0

    def _low_stock_representative_variant(self):
        """The variant a shop tile speaks for.

        A tile groups variants and shows the product name, not a variant
        name. The first variant is the one the tile opens with, so it is the
        one whose stock the badge states.
        """
        self.ensure_one()
        return self.product_variant_id

    def _low_stock_badge_values(self):
        self.ensure_one()
        variant = self._low_stock_representative_variant()
        if not variant:
            return empty_badge()
        return variant._low_stock_badge_values()

    def _get_combination_info(self, *args, **kwargs):
        """Let the product page render the badge without a second lookup.

        ``combination_info`` is already the one dict the page and the variant
        selector agree on, so the badge values ride along. Reading the
        variant back out of the dict matters: on a page opened with an
        attribute value, the template's first variant is not necessarily the
        one being displayed.
        """
        info = super()._get_combination_info(*args, **kwargs)
        variant = self.env["product.product"].browse(info.get("product_id") or 0).exists()
        if not variant:
            variant = self._low_stock_representative_variant()
        if variant:
            info.update(variant._low_stock_badge_values())
        else:
            info.update(empty_badge())
        return info
