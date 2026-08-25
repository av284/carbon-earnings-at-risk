import streamlit as st
import pandas as pd
import numpy as np

# Page configuration
st.set_page_config(page_title="Carbon Earnings-at-Risk Dashboard", layout="wide")

# Hide Streamlit watermark, footer, and top menu
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .stAppViewerFooter {display: none;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

st.title("Carbon Earnings-at-Risk Dashboard")
st.caption("Quantifying corporate EBITDA margin erosion across NGFS carbon tax trajectories ($0–$250/tCO2e).")

# Baseline Corporate Financial Database (Scope 1, Scope 2 in metric tons CO2e, Baseline EBITDA in $M)
#
# Sources (as of Aug 2026):
# - ExxonMobil: Scope 1/2 from ExxonMobil 2024 Sustainability/Metrics & Data disclosure
#   (91M t Scope 1 + 9M t Scope 2). EBITDA ~ FY2025 reported EBITDA (~$68B, varies ~$64-70B by provider).
# - Tesla: Scope 1/2 from Tesla 2024 Impact Report, operational emissions
#   (302k t Scope 1 + 754k t Scope 2). EBITDA ~ FY2025 GAAP-basis EBITDA (~$11.8B).
#   Note: Tesla's non-GAAP "Adjusted EBITDA" runs higher (~$15-17B TTM) - GAAP EBITDA used here for consistency.
# - Amazon: Scope 1/2 from Amazon 2024 Sustainability Report (market-based Scope 2 method, which
#   Amazon itself uses: 15.13M t Scope 1 + 2.80M t Scope 2). EBITDA = FY2025 reported EBITDA (~$165.3B).
# - American Airlines Group: Scope 1/2 from AAL 2024 GHG disclosure (39.95M t Scope 1 + 128k t Scope 2,
#   market-based). EBITDA estimated from FY2025 operating income + D&A (~$5.1B) given weak 2025 results
#   (TTM EBITDA has since compressed further due to fuel-cost pressure in 2026).
#
# EBITDA figures vary by data provider (GAAP vs. adjusted, fiscal-year vs. trailing-twelve-month) —
# treat these as reasonable midpoint estimates, not exact 10-K line items.
COMPANY_DATA = {
    "ExxonMobil (XOM)": {"sector": "Energy", "scope1": 91_000_000, "scope2": 9_000_000, "ebitda_m": 67_940},
    "Tesla Inc. (TSLA)": {"sector": "Automotive", "scope1": 302_000, "scope2": 754_000, "ebitda_m": 10_760},
    "Amazon.com (AMZN)": {"sector": "Consumer Discretionary", "scope1": 15_130_000, "scope2": 2_800_000, "ebitda_m": 168_910},
    "American Airlines (AAL)": {"sector": "Industrials", "scope1": 39_946_681, "scope2": 128_153, "ebitda_m": 3_370},
}

# Sidebar controls
st.sidebar.header("Scenario Controls")
company_choice = st.sidebar.selectbox("Select Equity", list(COMPANY_DATA.keys()))
carbon_tax = st.sidebar.slider("Carbon Tax Rate ($/tCO2e)", min_value=0, max_value=250, value=100, step=10)
pass_through = st.sidebar.slider("Consumer Pass-Through Rate (%)", min_value=0, max_value=100, value=25, step=5) / 100.0


def fmt_musd(value_m: float) -> str:
    """Format a $-millions figure as $B when >= $1,000M, otherwise as $M."""
    if abs(value_m) >= 1_000:
        return f"${value_m / 1_000:,.2f}B"
    return f"${value_m:,.1f}M"


# Stress-test calculation
comp = COMPANY_DATA[company_choice]
total_emissions = comp["scope1"] + comp["scope2"]
gross_carbon_cost_m = (total_emissions * carbon_tax) / 1_000_000
net_carbon_cost_m = gross_carbon_cost_m * (1.0 - pass_through)
post_tax_ebitda_m = max(0.0, comp["ebitda_m"] - net_carbon_cost_m)
ebitda_erosion_pct = (net_carbon_cost_m / comp["ebitda_m"]) * 100.0

# Display Top KPI Cards
col1, col2, col3, col4 = st.columns(4)
col1.metric("Baseline EBITDA", fmt_musd(comp["ebitda_m"]))
col2.metric("Net Carbon Cost", f"-{fmt_musd(net_carbon_cost_m)}")
col3.metric("Post-Tax EBITDA", fmt_musd(post_tax_ebitda_m))
col4.metric("EBITDA Erosion", f"{ebitda_erosion_pct:.1f}%")

st.divider()

# Build Scenario Data Table & Area Chart
prices = list(range(0, 260, 25))
trajectory_data = []
for p in prices:
    cost = ((total_emissions * p) / 1_000_000) * (1.0 - pass_through)
    rem_ebitda = max(0.0, comp["ebitda_m"] - cost)
    trajectory_data.append({"Carbon Tax ($/tCO2e)": p, "Remaining EBITDA ($M)": rem_ebitda})

df_chart = pd.DataFrame(trajectory_data).set_index("Carbon Tax ($/tCO2e)")

st.subheader(f"EBITDA Trajectory Analysis — {company_choice}")
st.area_chart(df_chart)
