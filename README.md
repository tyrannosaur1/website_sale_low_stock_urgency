# Low Stock Urgency Badges

Tell the shop when only a few are left: a configurable scarcity badge on the product page, the shop grid and the cart, measured on the quantity that can still be sold.

Odoo 11.0 – 20.0. One branch per series, the branch name is the series.

## What it does

- A threshold per product, per public category and per website; 0 passes the question down the line, so a category can set the rule once for everything in it.
- The badge states the sellable quantity, not the on-hand count that still includes stock already promised to other orders.
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

- **The sellable number on this series is `virtual_available`, not `free_qty`.** `free_qty` only arrives in 13.0. `virtual_available` is on hand plus incoming minus outgoing, so it does drop when a confirmed order creates its delivery move, but it does **not** drop when a reservation is written straight onto a quant with no move behind it. A shop that reserves stock by hand will therefore see the badge a little later than on 13.0 and up.
- 11.0 has no `_get_combination_info`, so the product page badge is rendered from `product.product_variant_id` — the variant the add-to-cart form posts. The stock sentence next to it is filled in by the shop's own script; the badge is a server-side addition and is not rewritten by that script.
- The cart badge is on the quantity cell. 11.0 has a single cart rendering, so there is no mobile duplicate to skip.
- 11.0 cannot resolve a *named* decimal precision inside a field definition, so the thresholds are declared with a fixed two-decimal scale instead of the `Product Unit of Measure` precision that 13.0 onwards can reference.
- 11.0 words its own stock line `3 Units available`; the duplicate check compares against that wording, not against the `Only 3 Units left in stock.` sentence that starts at 15.0.
- 11.0 has no `assets` manifest key, so the stylesheet is appended to the frontend bundle from a view.

## License

OPL-1. See `LICENSE`.

## Support

Open an issue on this repository.
