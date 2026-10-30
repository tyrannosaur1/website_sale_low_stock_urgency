# -*- coding: utf-8 -*-
{
    "name": "Low Stock Urgency Badges",
    "version": "10.0.1.0.0",
    "summary": "Show a configurable scarcity badge on the product page, the "
               "shop grid and the cart when a variant's sellable quantity "
               "reaches a threshold.",
    "author": "ModForge",
    "images": ["static/description/cover.png",
               "static/description/screenshot_1.png",
               "static/description/screenshot_2.png"],
    "license": "OPL-1",
    "category": "Website/Website",
    "depends": ["website_sale", "website_sale_stock"],
    "data": [
        "views/product_views.xml",
        "views/website_views.xml",
        "views/templates.xml",
    ],
    "installable": True,
    "application": False,
    "price": 19.0,
    "currency": "USD",
}
