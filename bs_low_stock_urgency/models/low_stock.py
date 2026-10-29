# -*- coding: utf-8 -*-
"""The scarcity badge: what makes it appear, and what keeps it quiet.

Two rules govern this file and both are about *not* showing something:

* a badge is only a statement about the **sellable** quantity, the number the
  shop can still promise, not ``qty_available``, which is the on-hand count
  and still includes stock already promised to other orders. 10.0 has no
  ``free_qty`` yet (it arrives in 13.0), so this series reads
  ``virtual_available``: on hand plus incoming minus outgoing, which does
  account for the delivery move a confirmed order created;
* core already prints an availability line next to the product. A badge that
  repeats that line word for word is noise, so the rendered text is compared
  with what core would print and dropped when the two agree. 10.0 has no
  quantity in that line at all -- it prints the fixed label ``In Stock`` or
  the merchant's own availability warning -- so the comparison can only catch
  a badge that copies one of those two.

This file stays Python 2.7 clean: no f-strings, no zero-argument ``super()``,
and every literal that ends up in a translatable field is a unicode string.
"""
from odoo import release

#: Shown when the website has no wording of its own left.
DEFAULT_BADGE_TEXT = u"Only {qty} left"
DEFAULT_CRITICAL_TEXT = u"Last few"


def series():
    """The major version of the running Odoo, e.g. ``10``."""
    return release.version_info[0]


def format_quantity(quantity):
    """A quantity as a customer reads it: 5, 0.25, 1.5 -- never ``5.0``."""
    value = float(quantity or 0.0)
    if value == int(value):
        return str(int(value))
    return ("%.6f" % value).rstrip("0").rstrip(".")


def is_stock_tracked(product):
    """Whether *product* is a storable good.

    10.0 spells it ``type='product'``; the ``is_storable`` flag only arrives
    with 18.0. A service or a consumable answers False.
    """
    return product.type == "product"


def sellable_quantity(product):
    """The number of units the shop can still promise.

    ``free_qty`` (on hand minus reserved) only exists from 13.0. On 10.0 the
    published figure is ``virtual_available`` -- on hand plus incoming minus
    outgoing -- which drops when a confirmed order creates its delivery move,
    but not when a reservation is written straight onto a quant without a
    move behind it.
    """
    return product.sudo().virtual_available


def normalize(text):
    """The form two sentences are compared in.

    Whitespace is collapsed because the same sentence is built from several
    template fragments, and a trailing period is not a difference a customer
    can see. ``str.casefold`` does not exist on Python 2, so this uses
    ``lower``: the texts compared here are ASCII.
    """
    return " ".join((text or "").split()).lower().rstrip(".").strip()


def translate(env, text):
    """Translate *text* with whichever accessor this series provides."""
    translator = getattr(env, "_", None)
    if callable(translator):
        return translator(text)
    from odoo import _
    return _(text)


def render_text(text, quantity):
    """Fill the ``{qty}`` placeholder, and survive a stray brace.

    A merchant sentence is free text. ``format`` raises on an unknown
    placeholder, and a badge that crashes the product page because somebody
    typed ``{qty`` is worse than a badge that prints the sentence as typed.
    """
    try:
        return text.format(qty=format_quantity(quantity))
    except (KeyError, IndexError, ValueError):
        return text


def core_availability_sentence(env, product, quantity):
    """What the shop prints next to the same variant, on this series.

    This is a copy of the shop's wording, not a replacement for it: core keeps
    rendering its own line and this string is only used to notice that the
    badge says exactly the same thing.

    10.0 renders no quantity: ``In Stock`` when the merchant ticked that
    box, otherwise the free-text availability warning, otherwise nothing.
    """
    template = product.sudo().product_tmpl_id
    if template.availability == "in_stock":
        return translate(env, u"In Stock")
    if template.availability == "warning":
        return template.availability_warning or u""
    return u""


def website_of(env):
    """The website a badge is read from, request or not.

    The current site is a model method that touches ``request``; outside a
    request that proxy raises ``RuntimeError`` (not ``AttributeError``), so
    the test environment needs the explicit fallback to the first site.
    """
    Website = env["website"]
    getter = getattr(Website, "get_current_website", None)
    if getter:
        try:
            website = getter()
        except RuntimeError:
            website = Website.browse()
        if website:
            return website
    return Website.search([], limit=1)


def empty_badge():
    """The shape every caller can read, badge or not."""
    return {
        "low_stock_badge_text": u"",
        "low_stock_badge_qty": 0.0,
        "low_stock_badge_critical": False,
    }
