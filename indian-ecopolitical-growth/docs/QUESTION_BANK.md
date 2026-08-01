# Question bank — top questions per analytical domain

_Every question below was checked against the actual data before being listed. Questions the data
cannot answer are in the rejected section at the bottom, with the reason — that list is as useful as
the accepted one._

Status: **built** (live in the app) · **ready** (data verified, not yet built) · **thin** (answerable
but on sparse data, needs a caveat)

---

## 1. Macro & growth

| Q | Question | Exposes | Status |
|---|---|---|---|
| Q1 | Does headline GDP flatter what reached each person? | Bias — population absorbs growth | **built** |
| Q4 | Which years are genuine shocks rather than noise? | Anomaly vs India's own norm | **built** |
| — | Is growth becoming less volatile, or just luckier? | Regime change — rolling 10y σ of growth | ready |
| — | Is inflation eating the growth? | Real vs nominal gap | ready |
| — | How much of "growth" is the base effect after a bad year? | Statistical artefact | ready |

## 2. Structure of the economy

| Q | Question | Exposes | Status |
|---|---|---|---|
| Q3 | Did India skip the manufacturing stage? | Structural weakness | **built** |
| — | Is the services share broad-based or concentrated? | Fragility of the growth engine | ✗ blocked — no sub-sector split |

## 3. Trade & external

| Q | Question | Exposes | Status |
|---|---|---|---|
| Q7 | Did 1991 actually open the economy, or was it already opening? | Whether the break is step or slope | **built** |
| Q10 | How close has India come to running out of foreign exchange? | Fragility — reserves in months of imports | **built** |
| — | Is India financing growth with foreign money or its own? | Dependence — FDI vs current account | ready |
| — | Has the rupee fallen faster than inflation justifies? | Real vs nominal depreciation | ready |
| — | Did trade openness peak in 2012 and reverse? | De-globalisation | ready (peak 56% in 2012 → 46% now) |

## 4. Fiscal & state capacity

| Q | Question | Exposes | Status |
|---|---|---|---|
| Q9 | Guns, books, or medicine — what does the state prioritise? | Revealed priorities | **built** |
| — | Does the state collect enough to fund what it promises? | Tax capacity vs spending | ready |
| — | Is the debt path sustainable? | Debt vs primary balance | ready (IMF, to 2031) |
| — | Does India pay more to borrow than it earns in growth? | r vs g — the debt-trap condition | ready |

## 5. Demography

| Q | Question | Exposes | Status |
|---|---|---|---|
| — | Is the demographic dividend arriving or already leaving? | Fertility + population growth decline | ready |
| — | Did health outcomes outrun income? (Preston curve) | Life expectancy vs GDP/capita | ready |
| — | Did urbanisation cause the services shift, or follow it? | Sequencing | ready |

## 6. Society & inclusion

| Q | Question | Exposes | Status |
|---|---|---|---|
| Q5 | Did growth actually reach women? | Bias — participation fell as GDP rose | **built** |
| Q8 | Which spread faster — the grid or the network? | Diffusion speed, state vs market | **built** |
| — | Does education spending translate into enrolment? | Spend → outcome gap | thin (edu spend 22 obs) |
| — | Did literacy gains keep pace with enrolment gains? | Quality vs access | thin (literacy 14 obs) |

## 7. Inequality & poverty

| Q | Question | Exposes | Status |
|---|---|---|---|
| — | Did growth reduce poverty, and at what rate per point of GDP? | Growth elasticity of poverty | thin (8 obs) |
| — | Has inequality moved at all through the whole boom? | Gini stability | thin (8 obs) |

⚠️ This is the weakest domain in the dataset — 17% year coverage. Q6 exists to say so out loud.

## 8. Environment & energy

| Q | Question | Exposes | Status |
|---|---|---|---|
| Q11 | Is growth decoupling from emissions? | Relative vs absolute decoupling | **built** |
| — | Is the renewables share rising fast enough to bend the curve? | Transition pace | ready |
| — | Did forest cover survive the growth decades? | Land-use tradeoff | ready |

## 9. Governance & democracy

| Q | Question | Exposes | Status |
|---|---|---|---|
| Q2 | Do prosperity and democratic depth move together? | The core eco-political claim | **built** |
| Q12 | Which part of democracy eroded first? | Sequencing of erosion | **built** |
| — | Do V-Dem and the World Bank's WGI tell the same story? | Cross-source validation, 1996+ | ready |
| — | Did governance quality track the reform decades? | Regulatory quality vs FDI | ready |

## 10. Evidence quality

| Q | Question | Exposes | Status |
|---|---|---|---|
| Q6 | Where is our evidence weakest? | Measurement bias | **built** |
| — | Which indicators stopped being collected, and when? | Series discontinuation | ready |

---

## Rejected — and why that matters

Checked against live data, found unanswerable. Listing these prevents re-proposing them.

| Question | Why it died |
|---|---|
| **Do the World Bank and IMF disagree about India?** | They don't. Mean absolute gap on GDP growth over 46 overlapping years is **0.00 points**, max 0.1. The WB sources from the IMF, so the chart would be a flat zero line. Killed after building the query, before building the chart. |
| Does employment follow output by sector? | No employment-by-sector series in the config; WB doesn't carry it for India at this granularity. |
| Is services growth broad or concentrated? | Requires sub-sector decomposition WB doesn't expose. |
| State-level divergence | National aggregates only. Needs MOSPI / data.gov.in — Tier 4, key-gated or scrape-only. |
| Monthly inflation / repo rate dynamics | Annual data only. Needs RBI, which has no API. |
| Ease of doing business trend | `IC.BUS.EASE.XQ` returns 0 rows — WB discontinued the index in 2021. |

---

## Next phase — LLM-generated finding lines

The current `finding()` per question is deterministic R that derives a sentence from the visible data.
An OpenRouter call is a **drop-in swap at exactly one seam**: each question already exposes
`finding(d) -> character(1)`, and the UI only ever renders that string.

Design constraints when it lands:

1. **Deterministic finding stays as the fallback.** No key, rate limit hit, or timeout should ever blank
   the line — the computed sentence is the floor, the model is an upgrade.
2. **Send numbers, not the chart.** Pass the aggregated series and the question text; a reasoning model
   given tabular facts will beat one guessing from an image, and it is far cheaper.
3. **The model must not invent figures.** Prompt it to interpret only supplied numbers. Ideally validate
   that every numeral in the response appears in the payload, and fall back if not.
4. **Cache by (question, year range).** The inputs are a tiny discrete space; an unkeyed call per
   reactive tick would burn a free tier in minutes.
