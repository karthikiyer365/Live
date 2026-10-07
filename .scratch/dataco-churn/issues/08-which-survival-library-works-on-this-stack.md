# Which survival library installs and runs on this repo's stack?

Type: research
Status: open
Blocked by: none

## Question

The project's other environments pin Python 3.12, pandas 3.0.6, numpy 2.x and scikit-learn 1.9. Which survival libraries (lifelines, scikit-survival, others) install and run Kaplan-Meier, a Cox model and a log-rank test on that stack? Report the working versions, any pandas 3 or numpy 2 breakage, and a fallback if none work (Kaplan-Meier by hand needs only numpy).

Resolved by reading each library's release notes, issue tracker and package metadata. Do not change the repo.
