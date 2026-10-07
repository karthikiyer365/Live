# How does a risk score become a retention list?

Type: grilling
Status: open
Blocked by: 02

## Question

A model gives each Active customer a risk score. What does the team do with it, given there is no experiment data?

Settle:
1. **List rule.** Top N, top decile, or a score threshold. What drives the choice (a review budget, a target precision)?
2. **Profit at risk table.** For the chosen list: customers, predicted Churned, Profit at risk captured, and how much Profit at risk sits in customers with negative profit (about 21% of customers lose money, and retaining them is not a goal).
3. **What is never claimed.** No "this campaign saves X". Only what is at risk and how well the model finds it.
4. **Calibration.** Whether the list uses calibrated probabilities, and what the calibrated ECE must be.

Blocked by the judging rules.
