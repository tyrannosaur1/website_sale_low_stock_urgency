# -*- coding: utf-8 -*-
"""The scarcity badge: what makes it appear, and what keeps it quiet.

Two rules govern this file and both are about *not* showing something:

* a badge is only a statement about the **sellable** quantity -- ``free_qty``,
  the number the shop can still promise, not ``qty_available``, which is the
  on-hand count and still includes stock reserved by other orders;
* core already prints an availability sentence next to the product. A badge
  that repeats that sentence word for word is noise, so the rendered text is
  compared with the sentence core would print and dropped when the two agree.

The comparison lives here rather than in the template because it has to know
how each series words its availability line, and that wording changed in
20.0.
"""
from odoo import release

#: Shown when the website has no wording of its own left.
DEFAULT_BADGE_TEXT = "Only {qty} left"
DEFAULT_CRITICAL_TEXT = "Last few"


def series():
    """The major version of the running Odoo, e.g. ``20``."""
    return release.version_info[0]


def format_quantity(quantity):
    """A quantity as a customer reads it: 5, 0.25, 1.5 -- never ``5.0``."""
    value = float(quantity or 0.0)
    if value == int(value):
        return str(int(value))
    return ("%.6f" % value).rstrip("0").rstrip(".")


def is_stock_tracked(product):
    """Whether *product* is a storable good on this series.

    Odoo 18 moved away from ``type='product'``: a stock-managed good is a
    ``consu`` with ``is_storable`` set. Asking both keeps the same test honest
    in every port; a service or a non-storable consumable answers False on
    all five.
    """
    return product.type == "product" or bool(getattr(product, "is_storable", False))


def normalize(text):
    """The form two sentences are compared in.

    Whitespace is collapsed because the same sentence is built from three
    template fragments and a trailing period is not a difference a customer
    can see. Nothing else is changed: two different sentences stay different.
    """
    return " ".join((text or "").split()).casefold().rstrip(".").strip()


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


def _uom_name(product):
    """The unit name the availability line prints, when it prints one.

    Until 19.0 the shop always had the unit at hand; 20.0 only sends it to the
    page when the Units of Measure group is enabled, so the sentence is
    shorter on a default database. Mirroring that keeps the duplicate check
    from comparing two sentences that are not the same one.
    """
    if series() >= 20:
        groups = product.env["res.groups"]
        enabled = getattr(groups, "_is_feature_enabled", None)
        if enabled and not enabled("uom.group_uom"):
            return ""
    # The unit of measure is not readable by a public visitor on every
    # series; the name is only a word in a sentence nobody is charged for.
    return product.sudo().uom_id.name or ""


def core_availability_sentence(env, product, quantity):
    """The sentence the stock module prints for the same variant.

    This is a copy of the shop's wording, not a replacement for it: core keeps
    rendering its own line and this string is only used to notice that the
    badge says exactly the same thing.

    16.0-19.0: ``Only 3 Units left in stock.``
    20.0:      ``3 Units in stock`` (the word "Only" was dropped when the
               line became a badge).
    """
    qty = format_quantity(quantity)
    uom = _uom_name(product)
    if series() >= 20:
        if uom:
            return translate(env, "%(qty)s %(uom)s in stock") % {"qty": qty, "uom": uom}
        return translate(env, "%(qty)s in stock") % {"qty": qty}
    return translate(env, "Only %(qty)s %(uom)s left in stock.") % {
        "qty": qty, "uom": uom}


def website_of(env):
    """The website a badge is read from, request or not.

    ``env.website`` exists from 20.0 on. Before that the current site is a
    model method that touches ``request``; outside a request that proxy raises
    ``RuntimeError`` (not ``AttributeError``), so the test environment needs
    the explicit fallback to the first site. The same fallback answers 20.0,
    which removed ``get_current_website`` altogether.
    """
    try:
        website = getattr(env, "website", None)
    except RuntimeError:
        website = None
    if website:
        return website
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
        "low_stock_badge_text": "",
        "low_stock_badge_qty": 0.0,
        "low_stock_badge_critical": False,
    }
