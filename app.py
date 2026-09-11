"""
Nassau Candy Distributor — Product Line Profitability & Margin Performance Dashboard
"""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Nassau Candy — Profitability Dashboard",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------
# Minimal, professional styling — no neon/gradients/glassmorphism.
# ----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .main { background-color: #FAFAFA; }
    h1, h2, h3 { color: #1F2A37; font-weight: 600; }
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 6px;
        padding: 14px 16px 8px 16px;
    }
    div[data-testid="stMetricLabel"] { color: #6B7280; }
    section[data-testid="stSidebar"] { background-color: #F3F4F6; }
    </style>
    """,
    unsafe_allow_html=True,
)

PALETTE = ["#3B5B92", "#5B8C5A", "#B5533C", "#7A6CA8", "#C9A15B"]


# ----------------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("data/cleaned_transactions.csv", parse_dates=["Order Date"])
    return df


try:
    df_raw = load_data()
except FileNotFoundError:
    st.error(
        "Could not find `data/cleaned_transactions.csv`. Run `notebooks/01_EDA_and_Cleaning.ipynb` "
        "first to generate the cleaned dataset."
    )
    st.stop()

if df_raw.empty:
    st.error("The cleaned dataset is empty.")
    st.stop()

MIN_DATE = df_raw["Order Date"].min().date()
MAX_DATE = df_raw["Order Date"].max().date()
ALL_DIVISIONS = sorted(df_raw["Division"].unique().tolist())

DEFAULTS = {
    "date_range": (MIN_DATE, MAX_DATE),
    "divisions": ALL_DIVISIONS,
    "margin_threshold": 0,
    "product_search": "",
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


def reset_filters():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v


# ----------------------------------------------------------------------------
# Sidebar filters
# ----------------------------------------------------------------------------
st.sidebar.title("Filters")

date_range = st.sidebar.date_input(
    "Order date range",
    min_value=MIN_DATE,
    max_value=MAX_DATE,
    key="date_range",
)

divisions = st.sidebar.multiselect(
    "Division",
    options=ALL_DIVISIONS,
    key="divisions",
)

margin_threshold = st.sidebar.slider(
    "Minimum gross margin % (product-level filter)",
    min_value=0,
    max_value=100,
    step=1,
    key="margin_threshold",
    help="Only products whose overall gross margin is at or above this value are shown.",
)

product_search = st.sidebar.text_input(
    "Search product name",
    key="product_search",
)

st.sidebar.button("Reset filters", on_click=reset_filters, width="stretch")

# ----------------------------------------------------------------------------
# Apply filters
# ----------------------------------------------------------------------------
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = MIN_DATE, MAX_DATE

mask = (
    (df_raw["Order Date"].dt.date >= start_date)
    & (df_raw["Order Date"].dt.date <= end_date)
    & (df_raw["Division"].isin(divisions if divisions else ALL_DIVISIONS))
)
df = df_raw.loc[mask].copy()

if product_search.strip():
    df = df[df["Product Name"].str.contains(product_search.strip(), case=False, na=False)]

# Product-level aggregation on the FILTERED data, then apply the margin-threshold filter
if not df.empty:
    product = (
        df.groupby(["Product ID", "Product Name", "Division"])
        .agg(Sales=("Sales", "sum"), Units=("Units", "sum"), Cost=("Cost", "sum"), Gross_Profit=("Gross Profit", "sum"))
        .reset_index()
    )
    product["Gross_Margin_Pct"] = product["Gross_Profit"] / product["Sales"].replace(0, np.nan) * 100
    product["Profit_Per_Unit"] = product["Gross_Profit"] / product["Units"].replace(0, np.nan)
    total_sales_all = product["Sales"].sum()
    total_profit_all = product["Gross_Profit"].sum()
    product["Revenue_Contribution_Pct"] = product["Sales"] / total_sales_all * 100 if total_sales_all else 0
    product["Profit_Contribution_Pct"] = product["Gross_Profit"] / total_profit_all * 100 if total_profit_all else 0
    product = product[product["Gross_Margin_Pct"].fillna(0) >= margin_threshold].reset_index(drop=True)
    # keep only filtered products' transactions for downstream charts consistency
    df = df[df["Product ID"].isin(product["Product ID"])].copy()
else:
    product = pd.DataFrame(
        columns=[
            "Product ID", "Product Name", "Division", "Sales", "Units", "Cost", "Gross_Profit",
            "Gross_Margin_Pct", "Profit_Per_Unit", "Revenue_Contribution_Pct", "Profit_Contribution_Pct",
        ]
    )

EMPTY_STATE = df.empty or product.empty

# ----------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------
st.title("Nassau Candy — Product Line Profitability & Margin Performance")
st.caption(
    "Turning raw transaction data into a profitability view: which products and divisions are "
    "actually financially valuable, not just high-volume."
)

if EMPTY_STATE:
    st.warning("No transactions match the current filters. Try widening the date range, adding divisions, "
               "lowering the margin threshold, or clearing the product search — or use **Reset filters**.")
    st.stop()

# ----------------------------------------------------------------------------
# Section 1 — KPIs + Product Profitability Overview
# ----------------------------------------------------------------------------
st.header("Product Profitability Overview")

total_sales = df["Sales"].sum()
total_profit = df["Gross Profit"].sum()
overall_margin = (total_profit / total_sales * 100) if total_sales else 0
total_units = df["Units"].sum()
n_products = product["Product ID"].nunique()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Sales", f"${total_sales:,.0f}")
k2.metric("Total Gross Profit", f"${total_profit:,.0f}")
k3.metric("Overall Gross Margin", f"{overall_margin:.1f}%")
k4.metric("Total Units", f"{total_units:,.0f}")
k5.metric("Products", f"{n_products}")

st.subheader("Product Profitability Leaderboard")
leaderboard = product.sort_values("Gross_Profit", ascending=False).reset_index(drop=True)
leaderboard.index = leaderboard.index + 1
st.dataframe(
    leaderboard[
        ["Product Name", "Division", "Sales", "Units", "Gross_Profit", "Gross_Margin_Pct",
         "Profit_Per_Unit", "Revenue_Contribution_Pct", "Profit_Contribution_Pct"]
    ].rename(columns={
        "Gross_Profit": "Gross Profit", "Gross_Margin_Pct": "Gross Margin %",
        "Profit_Per_Unit": "Profit / Unit", "Revenue_Contribution_Pct": "Revenue Contrib. %",
        "Profit_Contribution_Pct": "Profit Contrib. %",
    }).style.format({
        "Sales": "${:,.2f}", "Gross Profit": "${:,.2f}", "Gross Margin %": "{:.1f}%",
        "Profit / Unit": "${:,.2f}", "Revenue Contrib. %": "{:.1f}%", "Profit Contrib. %": "{:.1f}%",
    }),
    width="stretch",
    height=380,
)

c1, c2 = st.columns(2)
with c1:
    top_profit = product.sort_values("Gross_Profit", ascending=False).head(10)
    fig = px.bar(
        top_profit.sort_values("Gross_Profit"), x="Gross_Profit", y="Product Name", orientation="h",
        color_discrete_sequence=[PALETTE[0]], title="Top Products by Gross Profit",
        labels={"Gross_Profit": "Gross Profit ($)"},
    )
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, width="stretch")
with c2:
    top_margin = product.sort_values("Gross_Margin_Pct", ascending=False).head(10)
    fig = px.bar(
        top_margin.sort_values("Gross_Margin_Pct"), x="Gross_Margin_Pct", y="Product Name", orientation="h",
        color_discrete_sequence=[PALETTE[1]], title="Top Products by Gross Margin %",
        labels={"Gross_Margin_Pct": "Gross Margin (%)"},
    )
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, width="stretch")

st.subheader("High-Sales / Low-Margin Products")
sales_med = product["Sales"].median()
margin_med = product["Gross_Margin_Pct"].median()
hs_lm = product[(product["Sales"] >= sales_med) & (product["Gross_Margin_Pct"] < margin_med)].sort_values("Sales", ascending=False)
if hs_lm.empty:
    st.info("No products currently fall into the high-sales / low-margin quadrant under the active filters.")
else:
    st.dataframe(
        hs_lm[["Product Name", "Division", "Sales", "Gross_Margin_Pct"]].rename(
            columns={"Gross_Margin_Pct": "Gross Margin %"}
        ).style.format({"Sales": "${:,.2f}", "Gross Margin %": "{:.1f}%"}),
        width="stretch",
    )

# ----------------------------------------------------------------------------
# Section 2 — Division Performance
# ----------------------------------------------------------------------------
st.header("Division Performance")

division = (
    df.groupby("Division")
    .agg(Total_Sales=("Sales", "sum"), Total_Gross_Profit=("Gross Profit", "sum"), Total_Units=("Units", "sum"))
    .reset_index()
)
division["Avg_Gross_Margin_Pct"] = division["Total_Gross_Profit"] / division["Total_Sales"] * 100
d_total_sales = division["Total_Sales"].sum()
d_total_profit = division["Total_Gross_Profit"].sum()
division["Revenue_Contribution_Pct"] = division["Total_Sales"] / d_total_sales * 100 if d_total_sales else 0
division["Profit_Contribution_Pct"] = division["Total_Gross_Profit"] / d_total_profit * 100 if d_total_profit else 0
division = division.sort_values("Total_Sales", ascending=False)

d1, d2, d3 = st.columns(3)
with d1:
    fig = px.bar(division, x="Division", y="Total_Sales", color="Division",
                 color_discrete_sequence=PALETTE, title="Sales by Division",
                 labels={"Total_Sales": "Sales ($)"})
    fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, width="stretch")
with d2:
    fig = px.bar(division, x="Division", y="Total_Gross_Profit", color="Division",
                 color_discrete_sequence=PALETTE, title="Gross Profit by Division",
                 labels={"Total_Gross_Profit": "Gross Profit ($)"})
    fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, width="stretch")
with d3:
    fig = px.bar(division, x="Division", y="Avg_Gross_Margin_Pct", color="Division",
                 color_discrete_sequence=PALETTE, title="Gross Margin % by Division",
                 labels={"Avg_Gross_Margin_Pct": "Gross Margin (%)"})
    fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, width="stretch")

e1, e2 = st.columns(2)
with e1:
    comp = division.melt(
        id_vars="Division", value_vars=["Revenue_Contribution_Pct", "Profit_Contribution_Pct"],
        var_name="Metric", value_name="Percent",
    )
    comp["Metric"] = comp["Metric"].map({"Revenue_Contribution_Pct": "Revenue Contribution %",
                                          "Profit_Contribution_Pct": "Profit Contribution %"})
    fig = px.bar(comp, x="Division", y="Percent", color="Metric", barmode="group",
                 color_discrete_sequence=[PALETTE[0], PALETTE[1]], title="Revenue vs. Profit Contribution")
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, width="stretch")
with e2:
    fig = px.box(df, x="Division", y="Gross Profit", color="Division",
                 color_discrete_sequence=PALETTE, title="Gross Margin Distribution proxy (Gross Profit per line)",
                 points=False)
    fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, width="stretch")

# ----------------------------------------------------------------------------
# Section 3 — Cost vs Margin Diagnostics
# ----------------------------------------------------------------------------
st.header("Cost vs. Margin Diagnostics")

f1, f2 = st.columns(2)
with f1:
    fig = px.scatter(product, x="Cost", y="Sales", text="Product Name", color="Division",
                      color_discrete_sequence=PALETTE, title="Cost vs. Sales (by product)")
    fig.update_traces(textposition="top center", textfont_size=9)
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, width="stretch")
with f2:
    fig = px.scatter(product, x="Cost", y="Gross_Profit", text="Product Name", color="Division",
                      color_discrete_sequence=PALETTE, title="Cost vs. Gross Profit (by product)",
                      labels={"Gross_Profit": "Gross Profit ($)"})
    fig.update_traces(textposition="top center", textfont_size=9)
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, width="stretch")

g1, g2 = st.columns(2)
with g1:
    fig = px.histogram(product, x="Gross_Margin_Pct", nbins=10, color_discrete_sequence=[PALETTE[3]],
                        title="Gross Margin % Distribution Across Products",
                        labels={"Gross_Margin_Pct": "Gross Margin (%)"})
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, width="stretch")
with g2:
    st.markdown("**Margin-risk products (bottom quartile margin under current filters)**")
    if len(product) >= 4:
        cutoff = product["Gross_Margin_Pct"].quantile(0.25)
        risky = product[product["Gross_Margin_Pct"] <= cutoff].sort_values("Gross_Margin_Pct")
    else:
        risky = product.sort_values("Gross_Margin_Pct").head(1)
    st.dataframe(
        risky[["Product Name", "Division", "Sales", "Gross_Margin_Pct"]].rename(
            columns={"Gross_Margin_Pct": "Gross Margin %"}
        ).style.format({"Sales": "${:,.2f}", "Gross Margin %": "{:.1f}%"}),
        width="stretch", height=280,
    )

# ----------------------------------------------------------------------------
# Section 4 — Profit Concentration (Pareto)
# ----------------------------------------------------------------------------
st.header("Profit Concentration")

pareto_rev = product.sort_values("Sales", ascending=False).reset_index(drop=True)
pareto_rev["Cumulative_Pct"] = pareto_rev["Sales"].cumsum() / pareto_rev["Sales"].sum() * 100 if pareto_rev["Sales"].sum() else 0
n80_rev = int((pareto_rev["Cumulative_Pct"] < 80).sum() + 1) if not pareto_rev.empty else 0
pct80_rev = (n80_rev / len(pareto_rev) * 100) if len(pareto_rev) else 0

pareto_profit = product.sort_values("Gross_Profit", ascending=False).reset_index(drop=True)
pareto_profit["Cumulative_Pct"] = pareto_profit["Gross_Profit"].cumsum() / pareto_profit["Gross_Profit"].sum() * 100 if pareto_profit["Gross_Profit"].sum() else 0
n80_profit = int((pareto_profit["Cumulative_Pct"] < 80).sum() + 1) if not pareto_profit.empty else 0
pct80_profit = (n80_profit / len(pareto_profit) * 100) if len(pareto_profit) else 0

p1, p2 = st.columns(2)
p1.metric("Products generating 80% of Revenue", f"{n80_rev} of {len(pareto_rev)}", f"{pct80_rev:.0f}% of catalog")
p2.metric("Products generating 80% of Profit", f"{n80_profit} of {len(pareto_profit)}", f"{pct80_profit:.0f}% of catalog")

h1, h2 = st.columns(2)
with h1:
    fig = go.Figure()
    fig.add_bar(x=pareto_rev["Product Name"], y=pareto_rev["Sales"], name="Sales", marker_color=PALETTE[0])
    fig.add_trace(go.Scatter(x=pareto_rev["Product Name"], y=pareto_rev["Cumulative_Pct"],
                              name="Cumulative %", yaxis="y2", marker_color=PALETTE[2]))
    fig.add_hline(y=80, line_dash="dash", line_color="grey", yref="y2")
    fig.update_layout(
        title="Revenue Pareto", yaxis=dict(title="Sales ($)"),
        yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 105]),
        margin=dict(l=10, r=10, t=40, b=10), xaxis_tickangle=-90,
    )
    st.plotly_chart(fig, width="stretch")
with h2:
    fig = go.Figure()
    fig.add_bar(x=pareto_profit["Product Name"], y=pareto_profit["Gross_Profit"], name="Gross Profit", marker_color=PALETTE[1])
    fig.add_trace(go.Scatter(x=pareto_profit["Product Name"], y=pareto_profit["Cumulative_Pct"],
                              name="Cumulative %", yaxis="y2", marker_color=PALETTE[2]))
    fig.add_hline(y=80, line_dash="dash", line_color="grey", yref="y2")
    fig.update_layout(
        title="Gross Profit Pareto", yaxis=dict(title="Gross Profit ($)"),
        yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 105]),
        margin=dict(l=10, r=10, t=40, b=10), xaxis_tickangle=-90,
    )
    st.plotly_chart(fig, width="stretch")

st.caption(
    f"Under the current filters, {n80_rev} of {len(pareto_rev)} products drive 80% of revenue and "
    f"{n80_profit} of {len(pareto_profit)} products drive 80% of gross profit — a concentration signal, "
    "not a fixed company-wide figure, since it recalculates as filters change."
)

st.markdown("---")
st.caption("Nassau Candy Distributor internal analytics — internship project. All figures calculated from the uploaded transaction dataset.")
