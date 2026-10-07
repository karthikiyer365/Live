# How is the drift check designed?

Type: grilling
Status: open
Blocked by: 02

## Question

The headline benchmark uses one Cutoff, 2016-09-30. The drift check asks whether a model trained a year earlier still works.

Design: train features at Cutoff 2015-09-30 (label window to 2016-09-30), test at 2016-09-30 (label window to 2017-09-30). The churn rate is stable across Cutoffs (28.4–29.9%), so large drift is not expected.

Settle:
1. The metrics reported, against the benchmark's.
2. Customers appear at both Cutoffs: what is reported about that overlap?
3. What result would change a conclusion, and what would be written if drift is small.
4. Whether any intermediate Cutoffs (2016-03-31) are added as a trend line.

Blocked by the judging rules.
