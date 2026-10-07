# Which features may the model see at the Cutoff?

Type: grilling
Status: open
Blocked by: none

## Question

At the Cutoff (2016-09-30), which facts about an Active customer may the model use, and which are leakage?

Candidate feature families:
- **Recency, frequency, spend:** days since last Purchase, Purchase count, trailing and lifetime profit and sales (profit summed over Order lines).
- **Tenure:** days since first Purchase.
- **Reorder rhythm:** the customer's own median Reorder gap, and how overdue they are against it.
- **Discount depth:** `Order Item Discount Rate` history.
- **Shipping:** shipping-mode mix; delivery experience (real vs scheduled days) for Orders already delivered by the Cutoff.
- **Profile:** `Customer Segment`, market, region, department mix.

Settle:
1. Which families go in, and how each is computed so nothing after the Cutoff leaks in. Delivery experience needs a delivery date: the file has a shipping date and "days for shipping (real)", so an Order counts as delivered only if shipping date plus real days is on or before the Cutoff.
2. What is excluded and why: `Late_delivery_risk` (a formula of two columns), order status (not a lifecycle), and the personal-data columns (names, street, masked email and password).
3. Whether profit-based features risk circularity, since Profit at risk is also a reporting measure.

Output: an explicit feature list with a one-line leakage rule per family.
