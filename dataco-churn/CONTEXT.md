# DataCo Churn

Predicts which DataCo customers will stop buying, from their purchase history. The vocabulary below fixes what "customer", "purchase" and "churned" mean, because the DataCo file has several traps (one row per order line, a stretch of data with no returning customers, order statuses that are not a real lifecycle).

## Language

**Customer**:
A distinct Customer Id in the DataCo file.
_Avoid_: Client, user, account

**Order**:
A distinct Order Id. One Order holds one to five Order lines.
_Avoid_: Transaction, sale

**Order line**:
One row of the DataCo file: one product within an Order. Profit is recorded per Order line, so an Order's profit is the sum over its lines.
_Avoid_: Item, row, order item

**Purchase**:
An Order whose status is not CANCELED, SUSPECTED_FRAUD or PENDING_PAYMENT. Only Purchases count as customer activity.
_Avoid_: Sale, order (when activity is meant)

**Reorder gap**:
The number of days between two consecutive Purchases by the same Customer.
_Avoid_: Inter-purchase time, repeat interval

## Time

**Observation window**:
1 January 2015 to 30 September 2017, the only period in which Customers return.
_Avoid_: Training period, history

**Late-arrival block**:
1 October 2017 to 31 January 2018. It holds 8,322 Customers who each place exactly one Order and never return, so it is set aside and never modeled.
_Avoid_: New regime, second batch

**Cutoff**:
The date at which features stop and the Label window begins.
_Avoid_: Snapshot date, as-of date, split date

**Label window**:
The 365 days after the Cutoff, in which a Customer either makes a Purchase or does not.
_Avoid_: Horizon, prediction window

## Customers and outcomes

**Active customer**:
A Customer with at least one Purchase on or before the Cutoff.
_Avoid_: Eligible customer, existing customer

**Churned**:
An Active customer with no Purchase in the Label window.
_Avoid_: Lost, lapsed, attrited

**Profit at risk**:
The profit a Customer made in the 365 days before the Cutoff, summed over Order lines. It is the money lost if that Customer churns.
_Avoid_: CLV, revenue at risk, lifetime value
