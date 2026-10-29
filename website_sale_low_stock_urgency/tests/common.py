# -*- coding: utf-8 -*-
"""Small fixtures shared by the tests on every series.

Odoo 19 replaced ``type='product'`` with ``type='consu'`` plus
``is_storable``. The tests ask this helper instead of repeating the branch in
every fixture; the module code uses no such shortcut because it has to answer
for records the merchant already has.
"""
from odoo import release


def storable_product_values():
    """The fields that make a product a stock-managed good on this series."""
    if release.version_info[0] >= 18:
        return {"type": "consu", "is_storable": True}
    return {"type": "product"}


def untracked_product_values():
    """A consumable that does not manage stock, on every series."""
    return {"type": "consu"}
