# Nassau Candy Distributor — Product Line Profitability & Margin Performance Analysis

An end-to-end data analytics project turning raw Nassau Candy transaction data into a profitability
analysis and an interactive Streamlit dashboard.

## Business Problem

Sales volume alone does not tell Nassau Candy which products are financially valuable. Some products may
generate high sales but low profit, carry high costs against weak margins, or generate strong profit despite
lower sales volume. This project identifies which products and divisions actually drive company profit,
where margins are weak, and how concentrated revenue and profit are across the product catalog.

## Objective

1. Which products generate the most gross profit?
2. Which products have the highest gross margins?
3. Which high-sales products have weak margins?
4. Which divisions perform best financially, and which have weaker margins?
5. How concentrated is revenue and profit across products?
6. Which products show margin/cost risk, and which may deserve pricing, sourcing, or cost-review attention?

This is a data analytics / business analytics project. Machine learning was not forced into the analysis —
the dataset and objective are best served by profitability metrics, segmentation, and Pareto analysis.

## Dataset

`data/Nassau_Candy_Distributor.xlsx` — a single sheet of **10,194 order line items** across 18 columns:
order/customer/shipping metadata, product identifiers (Product ID, Product Name, Division), location
(Country, State, City, Postal Code, Region), and financials (Sales, Units, Cost, Gross Profit).

- **15 products** across **3 divisions**: Chocolate, Other, Sugar
- **4 regions**: Pacific, Atlantic, Interior, Gulf
- **2 countries**: United States, Canada
- Order dates span **2024-01-02 to 2025-12-31**

## Data Cleaning

- **No missing values** anywhere in the source data.
- **313 exact duplicate transaction rows** found (identical across every field except the surrogate Row ID,
  ~2.5% of total Sales dollars) — removed, keeping the first occurrence.
- **Order Date** was stored as a mix of native Excel dates and `DD-MM-YYYY` text strings within the same
  column; both were confirmed to represent the same underlying format and parsed into a single consistent
  datetime column.
- **Ship Date** was found to be unreliable — parsed values fall in 2026–2030, years after every Order Date —
  and was **excluded from all analysis** (it is not needed for the profitability objective; no delivery-time
  metrics are computed).
- **Gross Profit already existed** in the source data and was validated as exactly `Sales − Cost` for every
  row (max floating-point residual ~7e-15) — it was not recreated.
- No negative, zero, or otherwise invalid Sales, Units, Cost, or Gross Profit values were found.
- No factory location, coordinate, or shipping-route data exists in this dataset. The original project brief
  mentioned factory/shipping analysis, but since that data isn't present, it was correctly left out rather
  than fabricated — this project stays focused on product line profitability.

Cleaned output: **9,881 transaction rows** → `data/cleaned_transactions.csv`.

## Analytical Methodology & KPI Definitions

| Metric | Formula |
|---|---|
| Gross Profit | Sales − Cost (validated, not recreated) |
| Gross Margin % | Gross Profit / Sales × 100 |
| Profit Per Unit | Gross Profit / Units |
| Revenue Contribution % | Product Sales / Total Sales × 100 |
| Profit Contribution % | Product Gross Profit / Total Gross Profit × 100 |
| Margin Volatility | Std. deviation of a product's monthly gross margin over the 2-year window |

Product segmentation (High Performing / Margin Risk / Potential Opportunity / Requires Review) is based on
each product's Sales and Gross Margin relative to the **median** across the 15-product catalog — a
transparent, data-driven threshold, not an arbitrary cutoff. These are **review flags**, not automatic
business decisions.

## Product Analysis (key output: `data/product_profitability.csv`)

The five Wonka Bar chocolate SKUs are the clear financial core of the business:

| Product | Sales | Gross Profit | Gross Margin % |
|---|---|---|---|
| Wonka Bar – Triple Dazzle Caramel | $27,648.75 | $18,063.85 | 65.3% |
| Wonka Bar – Scrumdiddlyumptious | $27,028.80 | $18,770.00 | 69.4% |
| Wonka Bar – Milk Chocolate | $26,256.75 | $17,046.69 | 64.9% |
| Wonka Bar – Fudge Mallows | $24,361.20 | $16,240.80 | 66.7% |
| Wonka Bar – Nutty Crunch Surprise | $22,897.89 | $16,336.89 | 71.4% |

Outside the five Wonka Bars, **Kazookles** (Other division) stands out as a margin-risk product — meaningful
sales ($1,205.75) but only a **7.7% gross margin**, far below every other product in the catalog, making it
the clearest candidate for pricing or cost review. **Everlasting Gobstopper** (Sugar) has the single highest
gross margin (80.0%) but negligible sales volume ($130) — a "potential opportunity" product rather than a
current profit driver.

## Division Analysis

| Division | Total Sales | Total Gross Profit | Avg Gross Margin | Revenue Contribution | Profit Contribution |
|---|---|---|---|---|---|
| Chocolate | $128,193.39 | $86,458.23 | 67.4% | 92.7% | 94.9% |
| Other | $9,663.25 | $4,333.45 | 44.8% (pulled down by Kazookles' 7.7% margin) | 7.0% | 4.8% |
| Sugar | $427.48 | $284.73 | 66.6% (wide product-level range, 40–80%) | 0.3% | 0.3% |

Chocolate's profit contribution (94.9%) exceeds its revenue contribution (92.7%) — it converts sales to
profit slightly more efficiently than the catalog average. Other's profit contribution (4.8%) trails its
revenue contribution (7.0%), consistent with Kazookles dragging down that division's overall margin.

## Pareto (Concentration) Analysis

Calculated directly from the cleaned data:

- **5 of 15 products (33.3%)** generate the first **80% of total revenue**.
- **5 of 15 products (33.3%)** generate the first **80% of total gross profit**.
- In both cases, those 5 products are the Wonka Bar chocolate line.

**Business meaning:** Nassau Candy's financial performance is heavily concentrated in a third of its
catalog — specifically five chocolate SKUs. This indicates a dependency risk: a disruption to demand, cost,
or supply for any of these five products would have an outsized effect on total company revenue and profit,
while most of the remaining ten products (especially in the Sugar division) contribute only marginally in
dollar terms.

## Cost & Margin Diagnostics

Cost vs. Sales, Cost vs. Gross Profit, Cost vs. Margin, and Sales vs. Margin scatter plots (Notebook 3,
`images/cost_margin_diagnostics.png`) show the Wonka Bars clustered together with proportionally scaling
cost and profit, while Kazookles is a clear outlier: moderate cost relative to its low margin. These are
flagged as **review candidates**, not final recommendations — see Notebook 3 for the full, threshold-based
flag list (`data/cost_margin_flags.csv`).

## Dashboard Features (`app.py`)

A single-page Streamlit dashboard with four sections — Product Profitability Overview, Division Performance,
Cost vs. Margin Diagnostics, and Profit Concentration — plus working sidebar filters:

- Order date range
- Division multi-select
- Minimum gross margin % slider (product-level)
- Product name search
- Reset filters button

All KPIs, tables, charts, and rankings recompute from the filtered transaction set — nothing on the
dashboard shows stale/unfiltered data. An empty-filter state is handled with a clear message instead of a
broken layout.

## Interactive Live Dashboard

Explore the deployed Streamlit dashboard here:

**[Open the Interactive Live Dashboard](https://appuct-line-profitability-analysis.streamlit.app/)**

## Key Findings

- The business is a **chocolate-led company**: 96.6% of transaction lines and 92.7% of revenue come from the
  Chocolate division.
- Revenue and profit are both concentrated in **5 of 15 products (33.3% of the catalog)** — the Wonka Bar
  line.
- **Kazookles** is the clearest margin-risk product: real sales volume but a 7.7% gross margin, well below
  every other product.
- Chocolate converts revenue to profit slightly more efficiently than the company average (94.9% profit
  contribution vs. 92.7% revenue contribution); Other slightly less so, driven by Kazookles.
- Sugar-division products are individually high-margin in several cases (up to 80%) but contribute
  negligible dollars — they're a minor part of the business as currently sold, not a financial risk or driver
  either way.

## Recommendations

- Investigate Kazookles' cost structure and/or pricing — its margin is an outlier relative to the rest of
  the catalog.
- Given the concentration in five chocolate SKUs, treat supply, cost, and pricing stability for those
  products as a priority, since they carry the majority of company profit.
- Sugar-division products with strong per-unit margins (e.g., Everlasting Gobstopper, Hair Toffee) could be
  candidates for a volume/marketing push, since profitability per dollar is already strong — this is a
  data-supported opportunity flag, not a guaranteed outcome.

## Tech Stack

Python, pandas, numpy, matplotlib, seaborn, plotly, Streamlit, Jupyter.

## Project Structure

```
project/
├── data/
│   ├── Nassau_Candy_Distributor.xlsx      # original source file
│   ├── cleaned_transactions.csv           # output of Notebook 1
│   ├── product_profitability.csv          # output of Notebook 2
│   └── cost_margin_flags.csv              # output of Notebook 3
├── notebooks/
│   ├── 01_EDA_and_Cleaning.ipynb
│   ├── 02_Profitability_Analysis.ipynb
│   └── 03_Advanced_Analysis.ipynb
├── images/                                # chart exports from the notebooks
├── app.py                                 # Streamlit dashboard
├── requirements.txt
└── README.md
```

## Installation & Running

```bash
pip install -r requirements.txt

# Run the notebooks in order (each depends on the previous one's output):
jupyter nbconvert --to notebook --execute --inplace notebooks/01_EDA_and_Cleaning.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/02_Profitability_Analysis.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/03_Advanced_Analysis.ipynb

# Launch the dashboard:
streamlit run app.py
```

The dashboard reads `data/cleaned_transactions.csv`, so Notebook 1 must be run at least once before
`app.py`.

## Limitations

- Ship Date data quality issues meant delivery-time / shipping-efficiency analysis could not be included —
  it was not part of the stated objective, but is worth flagging if Nassau Candy wants that in a future
  version with corrected data.
- The catalog is small (15 products), so segmentation thresholds are based on medians/quartiles across those
  15 products rather than a larger statistical sample — reasonable for this dataset, but not something to
  over-interpret as a general industry benchmark.
- Margin volatility is measured only across the 2-year window present in the data; seasonality beyond that
  window can't be assessed.
- Screenshots of the running dashboard are not included in this README — run `streamlit run app.py` locally
  to view it live.

## Future Improvements

- If accurate shipping data becomes available, add a delivery-time / logistics-efficiency section.
- Add product-level cost breakdowns (e.g., ingredient vs. packaging vs. logistics) if that granularity
  becomes available, to make the cost-review flags more actionable.
- Extend the Pareto/segmentation logic to customer-level analysis (which customers/segments drive the most
  profit) if customer-level order history depth increases.