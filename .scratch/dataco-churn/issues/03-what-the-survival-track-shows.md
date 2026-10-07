# What does the survival track show, and how does it relate to the churn label?

Type: grilling
Status: open
Blocked by: 08

## Question

Design the Kaplan-Meier / Cox track that sits beside the fixed-window churn model.

Settle:
1. **The unit of time.** The Reorder gap is the duration. A customer whose last Purchase is within the data end (30 Sep 2017) is censored, not Churned. Is the clock restarted at every Purchase (recurrent gaps) or run once from the first Purchase?
2. **What is plotted.** Survival curves by segment, market, shipping mode and discount band; the point at which each curve crosses 365 and 450 days.
3. **Cox model.** Which covariates, and how the result is reported given an expected weak or null effect.
4. **The 450-day sensitivity.** How the survival track shows that a quarter of "Churned at 365 days" customers return within 450.
5. **Link to the churn model.** Whether survival output is a feature, a comparison, or only a sibling analysis.

Blocked by the library research: the answer to point 3 depends on which survival library installs on the project's pinned stack.
