# NSE Credit Risk Desk

A portfolio-level credit risk model for 10 NSE-listed companies, built end-to-end in Python. It estimates default probabilities from market data, prices expected loss, simulates correlated portfolio losses via Monte Carlo, and stress-tests the result under macro shocks.

**Pipeline:** Merton Structural Model &rarr; Expected Loss (PD x LGD x EAD) &rarr; Correlated Monte Carlo Simulation &rarr; Stress Testing &rarr; Excel Dashboard

Full methodology, formulas, and a detailed discussion of model limitations are in [`NSE_Credit_Risk_Desk_Methodology.docx`](NSE_Credit_Risk_Desk_Methodology.docx).

---

## What this project does

Given 10 NSE-listed companies and only public data (equity prices, market cap, total debt), the model answers three questions:

1. **How likely is each company to default?** Estimated via the Merton structural model, which treats equity as a call option on firm assets and solves for the unobservable asset value and asset volatility.
2. **How much would we lose on average?** Computed as Expected Loss = PD x LGD x EAD per company.
3. **How bad could it get, and how does that change in a crisis?** Estimated via a 10,000-path Monte Carlo simulation with correlated defaults, then re-run under three stress scenarios (rate spike, market crash, sector collapse).

## Portfolio

| Company | Sector | Ticker |
|---|---|---|
| Mahindra & Mahindra | Auto | M&M.NS |
| Adani Enterprises | Conglomerate / Infra | ADANIENT.NS |
| Zomato (Eternal) | Consumer Tech | ETERNAL.NS |
| JSW Steel | Metals | JSWSTEEL.NS |
| Vodafone Idea | Telecom | IDEA.NS |
| DLF | Real Estate | DLF.NS |
| IndiGo | Aviation | INDIGO.NS |
| Sun Pharma | Pharma | SUNPHARMA.NS |
| HDFC Bank | Banking | HDFCBANK.NS |
| Reliance Industries | Energy / Diversified | RELIANCE.NS |

Chosen to span 8+ sectors and a wide credit-quality range, from investment-grade blue chips to distressed, high-leverage names, so correlation and tail-risk effects in the simulation are economically meaningful.

## Repository structure

```
nse-credit-risk-desk/
|
├── merton_model.py          # Module 1: PD, DD, asset value/volatility per company
├── expected_loss.py         # Module 2: PD x LGD x EAD per company
├── portfolio_simulation.py  # Module 3: correlated Monte Carlo simulation, Credit VaR
├── stress_testing.py        # Module 4: rate spike, market crash, sector collapse scenarios
├── dashboard.py             # Module 5: multi-sheet Excel dashboard
|
├── data/                    # Generated CSVs and simulation output (created on run)
├── outputs/                 # Generated Excel dashboard (created on run)
|
└── NSE_Credit_Risk_Desk_Methodology.docx   # Full methodology, formulas, assumptions, limitations
```

## Methodology summary

### Module 1: Merton Structural Model

Equity is modeled as a call option on firm assets, with debt as the strike price. Given observable equity value (`E`), equity volatility (`σE`), debt (`D`), the risk-free rate (`r`), and a 1-year horizon (`T`), the model solves two equations simultaneously (via `scipy.optimize.fsolve`) for the unobservable asset value (`V`) and asset volatility (`σV`):

```
E = V·N(d1) − D·e^(−rT)·N(d2)          [Black-Scholes equity valuation]
σE·E = N(d1)·σV·V                       [links equity vol to asset vol]
```

From `V` and `σV`, Distance to Default and Probability of Default follow:

```
DD = [ln(V/D) + (r − 0.5σV²)T] / (σV√T)
PD = N(−DD)
```

### Module 2: Expected Loss

```
EL = PD × LGD × EAD
```

LGD is assigned per company by sector-level collateral reasoning (e.g., real estate = higher recovery, asset-light tech = lower recovery). EAD is an equal ₹100 crore notional per company.

### Module 3: Correlated Default Simulation

Since asset correlations are unobservable, equity return correlations are used as a proxy. The correlation matrix is Cholesky-decomposed (`L·Lᵀ = Σ`) to inject correlation into 10,000 simulated scenarios of independent standard normal shocks. In each scenario, a company defaults if its correlated shock falls below its PD-implied threshold; portfolio loss is summed across defaulted companies. From the resulting loss distribution: Expected Loss (mean), Credit VaR 99% (99th percentile), and Unexpected Loss (VaR minus EL).

### Module 4: Stress Testing

| Scenario | Shock | Rationale |
|---|---|---|
| Rate Spike | Risk-free rate to 9% | RBI emergency hike, higher debt servicing costs |
| Market Crash | Equity volatility x 1.5 | Broad volatility spike across all firms |
| Sector Collapse | LGD for Vodafone Idea and Adani to 90% | Telecom/infra-specific recovery deterioration |

### Module 5: Dashboard

All outputs are consolidated into `outputs/NSE_Credit_Risk_Desk.xlsx`, a 5-sheet workbook (Summary, Merton Results, Expected Loss, Stress Testing, Loss Distribution). Every figure in the Summary sheet is derived live from the underlying results, not hardcoded.

## Key results

| Scenario | Expected Loss | Credit VaR (99%) | Unexpected Loss |
|---|---|---|---|
| Baseline | ~₹73 lakh | ₹60 crore | ~₹59 crore |
| Rate Spike | ~₹68 lakh | ₹60 crore | ~₹59 crore |
| Market Crash | ~₹6 crore | ₹60 crore | ~₹54 crore |
| Sector Collapse | ~₹1.1 crore | ₹90 crore | ~₹89 crore |

Vodafone Idea dominates baseline PD and Expected Loss given its leverage and equity volatility. The Sector Collapse scenario produces the highest Credit VaR of all four scenarios, a 50% increase over baseline, despite affecting only 2 of 10 names, illustrating that concentration risk in already-weak names is more dangerous to portfolio tail risk than a broad, evenly distributed shock.

## How to run

```bash
pip install -r requirements.txt

python merton_model.py          # fetches data, solves Merton model, saves data/merton_results.csv
python expected_loss.py         # computes EL, saves data/expected_loss.csv
python portfolio_simulation.py  # runs Monte Carlo simulation, saves data/portfolio_losses.npy
python stress_testing.py        # runs stress scenarios, saves data/stress_results.csv
python dashboard.py             # builds outputs/NSE_Credit_Risk_Desk.xlsx
```

Each script imports objects from the ones before it (e.g., `stress_testing.py` imports `merton_df` from `merton_model.py`), so running any later script will also re-execute everything upstream of it. Running them in order, as above, avoids redundant work and produces all intermediate CSVs along the way.

## Known limitations

This model is a portfolio/learning project, not a production credit risk system. The most important limitations:

- The Merton model tends to underestimate PD for low-leverage, investment-grade firms (e.g., DLF, Sun Pharma), a well-documented characteristic of the vanilla structural model.
- Equity return correlations are used as a proxy for the unobservable asset return correlations.
- LGD assumptions are sector-level judgment calls, not calibrated from historical recovery-rate data.
- `yfinance`'s total debt figure for HDFC Bank includes customer deposits, which is not directly comparable to non-financial-firm borrowings.
- All 10 companies carry equal notional exposure, which understates real-world concentration risk.

The full list, with explanations, is in [`NSE_Credit_Risk_Desk_Methodology.docx`](NSE_Credit_Risk_Desk_Methodology.docx).

## Author

**Yusuf Sayeed**

Aspiring Market & Credit Risk Analyst | FRM Part 1 Cleared, FMVA Certified

- LinkedIn: [https://www.linkedin.com/in/yusuf-sayeed-fmva%C2%AE-711521315/]
- GitHub: [@Yusuf-Sayeed](https://github.com/Yusuf-Sayeed)
- Email: [sayeedyusuf03@gmail.com]

This project is part of a broader quantitative risk portfolio, alongside [NSE Risk Desk](https://github.com/Yusuf-Sayeed/NSE-Risk-Desk), a market risk engine covering VaR, Expected Shortfall, and stress testing for a 5-stock NSE equity portfolio.

## Tech stack

Python, NumPy, pandas, SciPy (`optimize`, `stats`), yfinance, openpyxl
