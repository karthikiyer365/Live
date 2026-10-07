# How is the model judged, and what must it beat?

Type: grilling
Status: open
Blocked by: none

## Question

Fix the scoring rules before any model is trained, as the ticket-type project did.

Settle:
1. **Headline metric and supporting ones.** PR-AUC (floor = the churn rate, about 29%), calibration error, lift in the top risk decile, and Profit at risk captured by the top decile.
2. **Baselines.** The rule "no Purchase for X days" (how is X chosen: on validation only?), then logistic regression on recency, frequency and spend. State what a gradient-boosting model must beat and by how much (a noise band, as the ticket project used 1 accuracy point; what is the equivalent for PR-AUC?).
3. **Splitting.** Customers split 71/14/14 stratified by Churned, sealed test, opened once. How uncertainty is shown (resampling customers).
4. **Selection rules written down now:** how ties are broken, which choices are made on validation only.

Output: the judging rules, in the same shape as the ticket project's "how models are judged" box.
