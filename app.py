import streamlit as st
import pandas as pd
import numpy as np

# Page configuration
st.set_page_config(page_title="Carbon Earnings-at-Risk Dashboard", layout="wide")

st.title("Carbon Earnings-at-Risk Dashboard")
st.caption("Quantifying corporate EBITDA margin erosion across NGFS carbon tax trajectories ($0–$250/tCO2e).")

# Baseline Corporate Financial Database (Scope 1, Scope 2, Baseline EBITDA in $M)
COMPANY_DATA = {
    "ExxonMobil (XOM)": {"sector": "Energy", "scope1": 110_000_000, "scope2": 9_000_000, "ebitda_m": 55_400},
    "Tesla Inc. (TSLA)": {"sector": "Automotive", "scope1": 400_000, "scope2": 800_000, "ebitda_m": 14_900},
    "Amazon.com (AMZN)": {"sector": "Consumer Discretionary", "scope1": 12_800_000, "scope2": 4_200_000, "ebitda_m": 85_500},
    "American Airlines (AAL)": {"sector": "Industrials", "scope1": 34_000_000, "scope2": 500_000, "ebitda_m": 5_300},
}

# Sidebar controls
st.sidebar.header("Scenario Controls")
company_choice = st.sidebar.selectbox("Select Equity", list(COMPANY_DATA.keys()))
carbon_tax = st.sidebar.slider("Carbon Tax Rate ($/tCO2e)", min_value=0, max_value=250, value=100, step=10)
pass_through = st.sidebar.slider("Consumer Pass-Through Rate (%)", min_value=0, max_value=100, value=25, step=5) / 100.0

# Stress-test calculation
comp = COMPANY_DATA[company_choice]
total_emissions = comp["scope1"] + comp["scope2"]
gross_carbon_cost_m = (total_emissions * carbon_tax) / 1_000_000
net_carbon_cost_m = gross_carbon_cost_m * (1.0 - pass_through)
post_tax_ebitda_m = max(0.0, comp["ebitda_m"] - net_carbon_cost_m)
ebitda_erosion_pct = (net_carbon_cost_m / comp["ebitda_m"]) * 100.0

# Display Top KPI Cards
col1, col2, col3, col4 = st.columns(4)
col1.metric("Baseline EBITDA", f"${comp['ebitda_m']:,}M")
col2.metric("Net Carbon Cost", f"-${net_carbon_cost_m:,.1f}M")
col3.metric("Post-Tax EBITDA", f"${post_tax_ebitda_m:,.1f}M")
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
