# Low Stock Urgency Badges

Tell the shop when only a few are left: a configurable scarcity badge on the product page, the shop grid and the cart, measured on the quantity that can still be sold.

Odoo 13.0 – 20.0. One branch per series, the branch name is the series.

## What it does

- A threshold per product, per public category and per website; 0 passes the question down the line, so a category can set the rule once for everything in it.
- The badge states `free_qty`, the sellable quantity, not the on-hand count that still includes stock already promised to other orders.
- Two sentences per website, translatable: a regular one that usually contains the number, and an urgent one used below a second, tighter threshold.
- The same badge on the product page next to the stock line, on the shop tile under the product name, and on each cart line for that line's own variant.
- Untracked products, products above the threshold, products with nothing left and a site with no threshold never show a badge.
- A badge whose text would repeat the stock sentence word for word is dropped rather than printed twice.

## Install

1. Copy the module into your addons path.
2. Update the app list, install **Low Stock Urgency Badges**.
3. Website › Configuration › Websites: open the site and set the threshold, the urgent threshold and the two sentences.
4. Sales › Products, or Website › Configuration › Product Categories: set a tighter number where it belongs.

## Notes

- The product page badge is rendered with the page for the variant the page opens with. The stock sentence next to it is filled in by the shop's own script when a visitor switches variant; the badge is a server-side addition and is not rewritten by that script.
- The cart badge is on the quantity cell. 13.0 has a single cart rendering, so there is no mobile duplicate to skip.
- The thresholds use the `Product Unit of Measure` decimal precision, which is what 13.0 calls the quantity precision that 16.0 renamed `Product Unit`.
- 13.0 words its own stock line `3 Units available`; the duplicate check compares against that wording, not against the `Only 3 Units left in stock.` sentence that starts at 15.0.
- 13.0 has no `assets` manifest key, so the stylesheet is appended to the frontend bundle from a view.
- `is_published` replaces `website_published` as the stored flag in 13.0, so a product published from the backend marks the right box; the tests still set `website_published`, which is kept as an alias on this series.

## License

OPL-1. See `LICENSE`.

## Support

Open an issue on this repository.
