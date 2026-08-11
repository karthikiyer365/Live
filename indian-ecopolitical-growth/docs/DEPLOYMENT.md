# Deployment

## The constraint

GitHub Pages, Vercel and Netlify all serve **static files only**. Shiny needs a running R
process, so the app cannot be hosted on any of them as an ordinary Shiny app.

The way round it is **shinylive**, which compiles the app to WebAssembly so R runs inside the
visitor's browser. No server, no cost, works on any static host.

## Status: working

| Step | Result |
|---|---|
| `arrow` available in webR? | ❌ **No** — swapped to `nanoparquet`, which is available and reads/writes the same format |
| ETL output after the swap | ✅ Identical — 4,355 rows, 64 indicators, 1789–2031, same PASS/WARN |
| `shinylive::export` | ✅ Builds, 119 MB / 228 files, no file over GitHub's 100 MB limit |
| R boots in the browser | ✅ Yes |
| Tabs, sidebar, KPIs, findings, dark theme | ✅ All correct |
| **Charts render** | ✅ **14 of 14, all 5 tabs. Fixed — see below.** |

### The blocker, and why the first two fixes missed

plotly's JS dependencies load *after* the first chart values arrive:

```
request 87  plotly-binding-4.12.0/plotly.js      200
request 101 crosstalk-1.2.2/js/crosstalk.min.js  200   <- too late
request 103 plotly-main-2.25.2/plotly-latest.min.js 200 <- too late
```

Every early widget throws `ReferenceError: crosstalk is not defined` and stays blank —
htmlwidgets calls `renderValue` once and never retries.

Two things made this harder than it looks, both confirmed by instrumenting the built export
in a real browser:

1. **The binding is fine.** The errors are thrown *inside* `renderValue`, so the output is
   bound and receiving values — only the globals are missing. Re-binding fixes nothing.
2. **You cannot gate the first render.** `plotly-latest.min.js` and `crosstalk.min.js` are
   widget-level dependencies delivered *with the first render payload*. Holding that render
   back with `req()` deadlocks: no render → no deps → nothing to wait for. Measured 0 of 5.

A fixed timer also cannot work — `plotly-latest.min.js` is ~3.5 MB out of the WASM
filesystem, so "long enough" is machine-dependent. A 15 s fallback still fired too early.

**The fix** (`app.R`): let the doomed first render happen — it is what ships the JS — then
watch the DOM and re-render only while a visible chart is still blank. The shim in the UI
head bumps a `plotly_ready` input, which every `renderPlotly` takes a reactive dependency on
(a plain reference, deliberately *not* `req()`). Self-terminating once everything paints.

### Verifying a change to that shim

Build and serve the export, then count painted widgets in the app iframe:

```r
shinylive::export("stage", "_site")
```
```js
// in the page console — 14 of 14 expected once all tabs have been visited
[...document.querySelector('iframe').contentDocument
    .querySelectorAll('.plotly.html-widget')]
  .filter(o => o.offsetParent !== null)
  .map(o => o.id + ':' + (o.querySelector('.plot-container') ? 'OK' : 'BLANK'))
```

A handful of `crosstalk is not defined` errors in the console is expected and harmless —
that is the first render, the one that delivers the JS. What matters is that no chart is
left `BLANK`.

## Options

| Option | Cost | Interactivity | Notes |
|---|---|---|---|
| **shinylive + static host** | free | full | In use. ~119 MB, slow first load |
| **shinyapps.io** | free tier | full | Real Shiny server — works today, no changes. 25 active hours/month |
| **Posit Connect Cloud** | free tier | full | Real server, deploys straight from the GitHub repo |
| **Swap plotly → ggplot2** | free | none (static images) | Renders server-side in WASM, sidesteps the JS race entirely. Loses hover/tooltips |

## GitHub Pages vs Vercel vs Netlify

You can host this **regardless of what else you already have on Pages** — GitHub gives every
repo its own project site (`<user>.github.io/<repo>/`). Pages is not currently enabled on this
repo; your other Pages sites are unaffected.

That said, **Vercel and Netlify are technically better for shinylive**, for one specific reason:

> webR runs faster when the page is *cross-origin isolated*, which requires the `COOP` and
> `COEP` response headers. **GitHub Pages cannot set custom headers.** Vercel (`vercel.json`)
> and Netlify (`netlify.toml`) both can.

Without those headers webR falls back to a slower execution path. All three are free and all
three will serve the 119 MB bundle.

## The workflow

`.github/workflows/deploy-dashboard.yml` builds and deploys to Pages. It uploads a Pages
artifact rather than committing the build, so the 119 MB of generated webR assets never enters
git history.

It is still **manual-only** (`workflow_dispatch`). The chart blocker that originally justified
that is fixed, so the commented-out `push` trigger is now safe to enable whenever you want
every merge to main to republish — uncomment it and nothing else changes.

Live at <https://karthikiyer365.github.io/ReLearning-Python/>.
