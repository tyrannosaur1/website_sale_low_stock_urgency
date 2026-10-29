# -*- coding: utf-8 -*-
from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    low_stock_threshold = fields.Float(
        "Low Stock Threshold", default=0.0, digits=(16, 2),
        help="Site-wide default for the scarcity badge. A product or its "
             "public category can set its own number; 0 here means the "
             "badge is off for products that do not set one.",
    )
    low_stock_critical_threshold = fields.Float(
        "Urgent Threshold", default=0.0, digits=(16, 2),
        help="When the sellable quantity is at or below this tighter number, "
             "the urgent text is used instead of the regular one. 0 keeps a "
             "single text for every badge.",
    )
    low_stock_badge_text = fields.Char(
        "Badge Text", default=u"Only {qty} left", translate=True,
        help="Text of the scarcity badge. {qty} is replaced with the "
             "sellable quantity. Leave empty for the default wording.",
    )
    low_stock_badge_critical_text = fields.Char(
        "Urgent Badge Text", default=u"Last few", translate=True,
        help="Text used at or below the urgent threshold. {qty} is optional "
             "here: an urgent badge often names no number at all.",
    )
