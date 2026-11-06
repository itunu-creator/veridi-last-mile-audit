# The "Last Mile" Logistics Auditor — Veridi Logistics

## A. Executive Summary

Veridi's delivery problem is **regional, not nationwide**: only 6.8% of 96,470 delivered orders arrive after the promised date, and the typical order arrives 12 days *early*, so the CEO's "wildly inaccurate estimates everywhere" hunch is not supported on average. The failures cluster in the **Northeast** (12.7% late, producing 17.6% of all late orders from 9.4% of volume; AL 21%, MA 17%, SE 15%) and in **Rio de Janeiro** (12.1% late, 22.9% of all late orders from 12.8% of volume), versus 4.5% in São Paulo. "Remote" is not the same as "worst": promised lead times scale almost perfectly with distance (Spearman ρ = +0.89) but late rate barely does (ρ = +0.25), because the far-North Amazon states already get 40+ day promises. Lateness drives sentiment: the average review falls from **4.29 (on time) to 2.99 (late) to 1.74 (super late)**, and on-time orders score 4.2+ in every region. The fix is to recalibrate ETAs state by state (about +12–13 days in the worst states for 95% on-time) and to attack the carrier leg, where late orders lose ~20 extra days versus ~3 for seller handling.

## B. Project Links

| Deliverable | Link |
|---|---|
| **Notebook (.ipynb)** | [`Veridi_Last_Mile_Audit.ipynb`](Veridi_Last_Mile_Audit.ipynb) (in this repo; open in Colab via *File → Open → GitHub* if a Colab link is required) |
| **Notebook (HTML export, charts visible)** | [`Veridi_Last_Mile_Audit.html`](Veridi_Last_Mile_Audit.html) |
| **Dashboard (public link)** | https://claude.ai/artifact/7Z6P4d6VG7B7Pj8pCECtz5 (source: [`dashboard.html`](dashboard.html)) |
| **Presentation (PDF)** | [`Veridi_Presentation.pdf`](Veridi_Presentation.pdf) · editable: [`Veridi_Presentation.pptx`](Veridi_Presentation.pptx) |
| **Video walkthrough (optional)** | not included |

## C. Technical Explanation

### Data cleaning (how and why)

| Issue found | Evidence | Decision |
|---|---|---|
| **Reviews are 1-to-many with orders** | 547 orders have 2+ reviews (551 surplus rows) | Kept the **most recent review per order** (`review_answer_timestamp`). Joined with `validate="1:1"` and an `assert len(master) == len(orders)` so a duplicate can never slip in silently. Master table = **99,441 rows**, identical to the orders table. |
| Orders without a review | 768 orders | Kept (score = NaN); averages ignore them. |
| Orders that can't be judged | 1,234 canceled/unavailable, 1,729 still in progress, 8 "delivered" with no delivery date | **Flagged** in `analysis_flag`, excluded from delay metrics, not deleted. **96,470** orders analysed. |
| Timestamp vs. date mismatch | Estimate is stored at `00:00:00`; delivery has a clock time | `Days_Difference` is computed on **calendar days** (`estimated − delivered`), so arriving on the promised date counts as on time. Raw timestamps would label ~1.3 pts more orders late (8.1% vs 6.8%), which would be unfair to Veridi. |
| Small samples | RR (41), AP (67), AC (80) orders | Shown but flagged `low_n` (n < 100) and excluded from headline rankings. |
| Portuguese categories | 73 categories; the official translation CSV covers 71 (lacks `pc_gamer` and one kitchen-appliance category); 610 products have no category | Official CSV used; my mapping fills the 2 gaps; products with no category kept as "Unknown / uncategorised". |

**Classification:** On Time (`Days_Difference ≥ 0`) · Late (1–5 days late) · Super Late (> 5 days late).

### Candidate's Choice: **Recalibrated ETA** (promise vs. reality, per state)

For each state I compute the number of days to add to today's promise so that **95% of historical orders would have arrived on time** (`max(0, −5th percentile of Days_Difference)`), plus a split of lead time into *seller handling* (purchase → carrier) and *carrier transit* (carrier → customer).

**Why it matters to the business:** the audit shows the failure is a *promise-setting* problem in specific places, not a universal speed problem. This turns the diagnosis into an action a CEO can approve today ("+13 days for AL/MA/CE; +12 for RJ"), shows that the **carrier leg**, not sellers, is where late orders lose time, and also reveals where Veridi *over-pads* (SP, MG, PR, RO, AM carry 11–20 days of cushion) and could promise faster to win sales. Caveat: computed in-sample, and longer promises may reduce conversion, so it should be piloted.

### Bonus: category translation and "is Furniture harder to ship than Electronics?"
Orders were linked to products through `olist_order_items_dataset.csv`, assigning each order its **primary category** (first item). This is safe: only 0.8% of orders span more than one category, and the join is asserted to keep one row per order.

| Group | Orders | % late | Expected late % (same states) | Avg days to deliver | Avg review |
|---|---|---|---|---|---|
| Electronics | 13,898 | 6.9% | 7.0% | 13.0 | 4.08 |
| Everything else | 74,339 | 6.7% | 6.7% | 12.2 | 4.19 |
| Furniture | 8,233 | 7.3% | 6.8% | 14.2 | 4.01 |

**Answer: only slightly.** Furniture is ~0.4 pt later than electronics overall (5.1% vs 4.2% within São Paulo) and takes ~1 extra day, but category is a **second-order driver**: categories range from ~4% to ~12% late, whereas states range from ~3% to ~21%. Product weight is not the driver (Spearman +0.09). *Audio* is the one clear category outlier (11.9% late, but only 344 orders). Fixing the Northeast and Rio matters far more than any product-specific fix.

### Other analytical notes
* **Remote-state test:** no seller-location file was provided, so distance is a *proxy*: great-circle km from São Paulo to each state capital.
* **Robustness:** on-time orders score 4.2–4.3 in every region, so low scores are caused by the delivery outcome, not by unhappy regions.
* **Time view:** late rate peaks in Mar 2018 (19.0%), Feb 2018 (14.1%) and Nov 2017 (12.4%), consistent with peak-season capacity strain.

### Known limitations (stated honestly)
* The ETA recalibration is descriptive, not causal, and longer promises may reduce conversion, so it should be piloted.
* No seller-location file was provided, so distance from the distribution centre is a proxy (São Paulo).
* Category results use each order's primary category; group definitions (Furniture = any "Furniture" category; Electronics = electronics, computers, telephony, audio, tablets) are listed in the notebook.

## How to reproduce

1. Download the Olist dataset from Kaggle and put the CSVs **in the same folder as the notebook** (no absolute paths anywhere). Required: orders, reviews, customers, products. For the category bonus also add `olist_order_items_dataset.csv` and `product_category_name_translation.csv` (the notebook skips that step cleanly if they are absent).
2. `pip install pandas numpy matplotlib jupyter`
3. Run `Veridi_Last_Mile_Audit.ipynb` top to bottom. It regenerates `figures/` and `dashboard_data.json`, which feeds the dashboard.

## Repository contents

```
Veridi_Last_Mile_Audit.ipynb   executed notebook (Stories 1–4, bonus, candidate's choice)
Veridi_Last_Mile_Audit.html    HTML export of the notebook, charts included
dashboard.html                 self-contained interactive dashboard (source of the public link)
dashboard_data.json            aggregates exported by the notebook (small; raw data is NOT committed)
Veridi_Presentation.pdf/.pptx  7-slide insight deck
figures/                       chart PNGs
.gitignore                     keeps the large raw CSVs out of the repo
```

## Pre-submission checklist

- [ ] GitHub repo is **public** (check in a private/incognito window)
- [ ] `.ipynb` **and** HTML export uploaded
- [ ] Raw CSVs **not** committed (`.gitignore` included)
- [ ] Dashboard link opens **without login** in incognito (the link is private until you use *Share* on the published page)
- [ ] Presentation link/file opens without login
- [ ] README links updated with your repo URL
