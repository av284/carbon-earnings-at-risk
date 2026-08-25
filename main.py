from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import matplotlib.pyplot as plt
import io, base64

app = FastAPI()

COMPANY_DATA = {
    "ExxonMobil (XOM)": {"sector": "Energy", "scope1": 91_000_000, "scope2": 9_000_000, "ebitda_m": 67_940},
    "Tesla Inc. (TSLA)": {"sector": "Automotive", "scope1": 302_000, "scope2": 754_000, "ebitda_m": 10_760},
    "Amazon.com (AMZN)": {"sector": "Consumer Discretionary", "scope1": 15_130_000, "scope2": 2_800_000, "ebitda_m": 168_910},
    "American Airlines (AAL)": {"sector": "Industrials", "scope1": 39_946_681, "scope2": 128_153, "ebitda_m": 3_370},
}

def fmt_musd(value_m: float) -> str:
    if abs(value_m) >= 1_000:
        return f"${value_m / 1_000:,.2f}B"
    return f"${value_m:,.1f}M"

class CalcRequest(BaseModel):
    company: str
    tax: float
    pass_through: float

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Carbon Earnings-at-Risk Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-black text-white font-sans antialiased">
    <div class="flex min-h-screen">
        <aside class="w-80 bg-zinc-950 p-6 border-r border-zinc-800 flex flex-col space-y-6">
            <h2 class="text-lg font-bold text-zinc-100">Scenario Controls</h2>
            <div>
                <label class="block text-xs text-zinc-400 mb-2">Select Equity</label>
                <select id="equitySelect" class="w-full bg-zinc-900 border border-zinc-800 rounded px-3 py-2 text-sm text-zinc-200 focus:outline-none">
                    {% for company in companies %}
                    <option value="{{ company }}">{{ company }}</option>
                    {% endfor %}
                </select>
            </div>
            <div>
                <div class="flex justify-between text-xs text-zinc-400 mb-2">
                    <span>Carbon Tax Rate ($/tCO2e)</span>
                    <span id="taxVal" class="text-emerald-400 font-semibold">$100</span>
                </div>
                <input type="range" id="taxInput" min="0" max="250" value="100" step="10" class="w-full accent-emerald-500">
            </div>
            <div>
                <div class="flex justify-between text-xs text-zinc-400 mb-2">
                    <span>Consumer Pass-Through Rate</span>
                    <span id="passVal" class="text-emerald-400 font-semibold">25%</span>
                </div>
                <input type="range" id="passInput" min="0" max="100" value="25" step="5" class="w-full accent-emerald-500">
            </div>
        </aside>

        <main class="flex-1 p-8 space-y-8 bg-black">
            <div>
                <h1 class="text-3xl font-bold tracking-tight text-zinc-50">Carbon Earnings-at-Risk Dashboard</h1>
                <p class="text-sm text-zinc-400 mt-1">Quantifying corporate EBITDA margin erosion across NGFS carbon tax trajectories ($0–$250/tCO2e).</p>
            </div>

            <div class="grid grid-cols-4 gap-4">
                <div class="bg-zinc-950 border border-zinc-800 rounded-lg p-5">
                    <span class="text-xs text-zinc-500 uppercase tracking-wider font-medium">Baseline EBITDA</span>
                    <div id="baseEbitdaCard" class="text-2xl font-semibold text-zinc-100 mt-2">--</div>
                </div>
                <div class="bg-zinc-950 border border-zinc-800 rounded-lg p-5">
                    <span class="text-xs text-zinc-500 uppercase tracking-wider font-medium">Net Carbon Cost</span>
                    <div id="netCostCard" class="text-2xl font-semibold text-red-400 mt-2">--</div>
                </div>
                <div class="bg-zinc-950 border border-zinc-800 rounded-lg p-5">
                    <span class="text-xs text-zinc-500 uppercase tracking-wider font-medium">Post-Tax EBITDA</span>
                    <div id="postEbitdaCard" class="text-2xl font-semibold text-zinc-100 mt-2">--</div>
                </div>
                <div class="bg-zinc-950 border border-zinc-800 rounded-lg p-5">
                    <span class="text-xs text-zinc-500 uppercase tracking-wider font-medium">EBITDA Erosion</span>
                    <div id="erosionCard" class="text-2xl font-semibold text-amber-400 mt-2">--</div>
                </div>
            </div>

            <div class="bg-zinc-950 border border-zinc-800 rounded-lg p-6">
                <h3 id="chartTitle" class="text-sm font-semibold text-zinc-300 mb-6">EBITDA Trajectory Analysis</h3>
                <div id="chartContainer" class="w-full flex justify-center"></div>
            </div>
        </main>
    </div>

    <script>
        async function updateDashboard() {
            const company = document.getElementById('equitySelect').value;
            const tax = document.getElementById('taxInput').value;
            const pass_through = document.getElementById('passInput').value;

            document.getElementById('taxVal').innerText = `$${tax}`;
            document.getElementById('passVal').innerText = `${pass_through}%`;

            const res = await fetch('/api/calculate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ company, tax: parseFloat(tax), pass_through: parseFloat(pass_through) })
            });

            const data = await res.json();
            document.getElementById('baseEbitdaCard').innerText = data.base_ebitda;
            document.getElementById('netCostCard').innerText = `-${data.net_cost}`;
            document.getElementById('postEbitdaCard').innerText = data.post_ebitda;
            document.getElementById('erosionCard').innerText = data.erosion;
            document.getElementById('chartTitle').innerText = `EBITDA Trajectory Analysis — ${company}`;
            document.getElementById('chartContainer').innerHTML = `<img src="data:image/png;base64,${data.chart}" class="max-w-full h-auto"/>`;
        }

        document.getElementById('equitySelect').addEventListener('change', updateDashboard);
        document.getElementById('taxInput').addEventListener('input', updateDashboard);
        document.getElementById('passInput').addEventListener('input', updateDashboard);
        updateDashboard();
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def read_root():
    from jinja2 import Template
    template = Template(HTML_CONTENT)
    return template.render(companies=list(COMPANY_DATA.keys()))

@app.post("/api/calculate")
async def calculate(data: CalcRequest):
    comp = COMPANY_DATA[data.company]
    pass_through = data.pass_through / 100.0
    total_emissions = comp["scope1"] + comp["scope2"]
    
    gross_carbon_cost_m = (total_emissions * data.tax) / 1_000_000
    net_carbon_cost_m = gross_carbon_cost_m * (1.0 - pass_through)
    post_tax_ebitda_m = max(0.0, comp["ebitda_m"] - net_carbon_cost_m)
    ebitda_erosion_pct = (net_carbon_cost_m / comp["ebitda_m"]) * 100.0

    prices = list(range(0, 260, 25))
    remaining_ebitda = [max(0.0, comp["ebitda_m"] - (((total_emissions * p) / 1_000_000) * (1.0 - pass_through))) for p in prices]

    plt.close('all')
    fig, ax = plt.subplots(figsize=(8.5, 3.5), facecolor='#09090b')
    ax.set_facecolor('#09090b')
    ax.plot(prices, remaining_ebitda, color='#10b981', linewidth=2)
    ax.fill_between(prices, remaining_ebitda, color='#10b981', alpha=0.15)
    ax.tick_params(colors='#71717a', labelsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#27272a')
    ax.spines['bottom'].set_color('#27272a')
    ax.grid(True, color='#27272a', linestyle='--', linewidth=0.5)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    buf.seek(0)
    chart_base64 = base64.b64encode(buf.read()).decode('utf-8')

    return JSONResponse({
        "base_ebitda": fmt_musd(comp["ebitda_m"]),
        "net_cost": fmt_musd(net_carbon_cost_m),
        "post_ebitda": fmt_musd(post_tax_ebitda_m),
        "erosion": f"{ebitda_erosion_pct:.1f}%",
        "chart": chart_base64
    })
