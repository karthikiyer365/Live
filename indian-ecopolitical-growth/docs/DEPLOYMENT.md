# Deployment

## The constraint

GitHub Pages, Vercel and Netlify all serve **static files only**. Shiny needs a running R
process, so the app cannot be hosted on any of them as an ordinary Shiny app.

The way round it is **shinylive**, which compiles the app to WebAssembly so R runs inside the
visitor's browser. No server, no cost, works on any static host.

## Status: partly working

| Step | Result |
|---|---|
| `arrow` available in webR? | ❌ **No** — swapped to `nanoparquet`, which is available and reads/writes the same format |
| ETL output after the swap | ✅ Identical — 4,355 rows, 64 indicators, 1789–2031, same PASS/WARN |
| `shinylive::export` | ✅ Builds, 119 MB / 228 files, no file over GitHub's 100 MB limit |
| R boots in the browser | ✅ Yes |
| Tabs, sidebar, KPIs, findings, dark theme | ✅ All correct |
| **Charts render** | ❌ **1 of 5 paints. This is the blocker.** |

### The blocker, precisely

plotly's JS dependencies load *after* the widget bindings try to run:

```
request 87  plotly-binding-4.12.0/plotly.js      200
request 101 crosstalk-1.2.2/js/crosstalk.min.js  200   <- too late
request 103 plotly-main-2.25.2/plotly-latest.min.js 200 <- too late
```

Every early widget throws `ReferenceError: crosstalk is not defined` and stays permanently
blank. `Plotly` and `crosstalk` *are* defined on `window` afterwards, but a widget that threw
never retries, and a resize event does not revive it.

**Tried and failed:**
1. Dispatching a `resize` on the app frame — no effect, the widget never initialised.
2. Forcing one re-render 2.5 s after boot via a `reactiveVal` bumped on a timer — the
   re-render fired (error count rose 4 → 9) but `crosstalk` still was not defined at that point.

**Not yet tried:** pre-loading the htmlwidgets dependencies by mounting one throwaway plotly
widget in the UI, so the JS is in place before the real charts render. This is the most likely
fix — the one chart that *does* paint is simply the one that happened to render after the
libraries arrived.

## Options

| Option | Cost | Interactivity | Notes |
|---|---|---|---|
| **shinylive + static host** | free | full, once fixed | Needs the plotly fix above. ~119 MB, slow first load |
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

`.github/workflows/deploy-dashboard.yml` builds and deploys to Pages. It is **manual-only**
(`workflow_dispatch`) — the push trigger is commented out deliberately so nothing auto-publishes
while charts render blank. It uploads a Pages artifact rather than committing the build, so the
119 MB of generated webR assets never enters git history.
