# Accessibility Audit: SICTrA Design Console v0.1

**Standard:** WCAG 2.1 AA | **Date:** 2026-08-30  
**Scope:** local read model, desktop 1440×1000, mobile 390×844 and an
automated Edge probe at 640×720 (1280px at 200% equivalent).

## Summary

**Confirmed issues after repair:** 0 critical, 0 major.  
**Validation boundary:** `PROBABLE / B`; manual screen-reader and 200% browser
zoom testing remain required before an AA claim.

## Findings

| Area | Verified result | WCAG |
|---|---|---|
| Structure | main/nav/asides/headings and explicit boundary text | 1.3.1 |
| Keyboard | skip link first; Enter focuses Studio; controls are native buttons | 2.1.1, 2.4.3 |
| Focus | 3px visible outline with offset | 2.4.7 |
| Targets | refresh 44px; mobile navigation 48px; stage controls 54px+ | 2.5.5 |
| Status/errors | polite live regions and alert; project missing returns explicit 404 | 3.3.1, 4.1.2 |
| Motion | reduced-motion media query disables animation/transition | 2.3.3 supporting |
| Reflow | 390px viewport has 0px global overflow; Ribbon scroll is localized | 1.4.10 supporting |
| 200% equivalent | 640px viewport has `scrollWidth == clientWidth == 640` | 1.4.10 |
| Accessible names | 47 visible controls across Studio/Create/Ops; 0 nameless | 3.3.2, 4.1.2 |
| Interactive targets | 0 non-checkbox controls below 44×44 in the automated probe | 2.5.5 |
| Mode access | Create and Ops both reachable and visible through native buttons | 2.1.1 |
| Forced colors | explicit `forced-colors: active` borders and active outline | 1.4.11 supporting |

## Color contrast

| Element | Foreground / background | Ratio | Required | Result |
|---|---|---:|---:|---|
| Body ink | `#182033 / #FFFFFF` | 16.24:1 | 4.5:1 | PASS |
| Muted copy | `#58647B / #FFFFFF` | 5.96:1 | 4.5:1 | PASS |
| Cobalt label | `#3157D5 / #FFFFFF` | 6.08:1 | 4.5:1 | PASS |
| Button | `#FFFFFF / #3157D5` | 6.08:1 | 4.5:1 | PASS |
| Rail | `#FFFFFF / #111C36` | 16.89:1 | 4.5:1 | PASS |
| State chip | `#605022 / #FFF6DD` | 7.30:1 | 4.5:1 | PASS |

## Remaining manual checks

1. NVDA and VoiceOver reading order, live announcements and disabled modes.
2. Text-only resize in a manually controlled browser session.
3. Windows High Contrast visual inspection with a human operator.
4. Cognitive review of technical labels with representative designers.

## Executable probe delta — 2026-08-31

`tools/block2_accessibility_probe.js` executed against the local server in
Microsoft Edge. It verified zero global overflow, the skip-link target,
Create/Ops reachability, reduced-motion activation, names for every visible
control and minimum target size. Result: `PASS` for this automated scope.

This is a separate browser oracle, not a substitute for NVDA/VoiceOver or a
human accessibility acceptance review.

## Keyboard traversal delta — 2026-09-02

`tools/block2_console_accessibility_probe.py` now creates una instancia local
temporal de la consola y ejecuta el probe Edge sin depender de un servidor
manual. Además del alcance anterior, recorre los stops de teclado de Studio,
Create y Ops: 42 stops observados, 0 ocultos y 0 sin nombre. Conserva los
resultados anteriores: 47 controles visibles, 0 targets insuficientes, 0px de
overflow, skip-link hacia `#studio`, Create/Ops alcanzables y motion reducido
activo.

Esto es `VERIFIED / A` sólo como recorrido browser automatizado de la fixture
sintética. El protocolo humano sigue en
`architecture/block2_assistive_review_protocol_v0.1.md`; no se promueve WCAG
AA, review asistiva ni aceptación.
