# Telecare OS shared shell

Owner reference: supplied September 13 image; implementation authorization
includes same-tab navigation, line icons and consistent styling across blocks.
No additional visual approval requested. Planning/implementation are split into
UI navigation first and autonomous runtime integration afterwards.

Palette: navy #10254b, cobalt #0754d4, turquoise #00b6ab, ink #112455,
paper #f7f9fc, dividers #d6dce6. Bahnschrift display, Segoe UI body and existing
monospace evidence identifiers. Signature: port imagery and a navy icon rail
connect editorial evidence to its local workspaces.

Selected approach: same-tab links between existing loopback services with shared
same-origin CSS and SVG symbols. A reverse proxy or embedded iframe was not
selected: these require new routing/security contracts or conflict with existing
frame restrictions. Same-tab navigation does not itself create a common runtime.

Retain all functional view IDs, keyboard labels, failure states and authority
boundaries. Replace decorative numbered navigation with recognizable icons,
but retain numbering when it represents an actual stage sequence. Never copy
illustrative counts, approval claims or uncertainty scores from the mockup.

Self-review: common shell must not erase each block's distinct workflow;
status colors remain semantic. At mobile widths block links remain visible and
local-view navigation scrolls horizontally. Shared assets must be packaged in
installable distributions, not rely on working-tree-only files.

Verification: parse all four HTML files for same-tab links and labeled SVG
navigation, request shared assets from all HTTP servers, reject arbitrary asset
paths, exercise navigation in one browser page with no popup, and run responsive
browser checks plus full regression. Runtime integration remains tracked in the
existing closure ledger; this visual increment does not complete that item.
