# Corporate Carbon Earnings-at-Risk Dashboard

An interactive financial stress-testing engine built with FastAPI, Tailwind CSS, and Matplotlib. The platform models Network for Greening the Financial System (NGFS) transition risk scenarios ($0–$250/tCO2e carbon tax trajectories) against corporate Scope 1 and Scope 2 emissions data to quantify EBITDA margin compression, cost absorption, and pass-through sensitivity across targeted public equities.

## Live Application
https://carbon-earnings-at-risk.vercel.app/

## Key Features
* **Emissions Ingestion:** Evaluates corporate Scope 1 & 2 carbon footprints ($tCO_2e$) against operational baseline EBITDA.
* **Sensitivity Modeling:** Custom scenario parameters for consumer carbon cost pass-through rates ($0\%–100\%$).
* **Margin Impact Analysis:** Real-time calculation of EBITDA erosion percentages and post-tax operational cash flows.
* **Trajectory Mapping:** Visual sensitivity curves mapping corporate earnings decline under incremental regulatory carbon pricing shocks.
