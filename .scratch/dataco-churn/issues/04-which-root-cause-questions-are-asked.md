# Which root-cause questions are asked, and how are null results reported?

Type: grilling
Status: open
Blocked by: 01

## Question

The user wants "why do customers leave", and the data is synthetic. A first late Order changes the repeat rate by almost nothing (57.2% vs 56.8%). Fix the honest version of root-cause analysis.

Settle:
1. **Exposures to test:** a late first Order, average lateness, shipping mode, discount depth, region, segment.
2. **Method:** compare repeat rates with confidence intervals, then an adjusted logistic regression. What counts as a finding, and what counts as "no effect".
3. **Wording.** The report states what the data cannot show (no experiment, synthetic data, lateness is a formula of two columns). Draft the sentence that frames a null result as a result.
4. **Where it sits** in the notebook relative to the model.

Blocked by the feature list: the exposures must use only information the feature rules allow.
