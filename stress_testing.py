#!/usr/bin/env python
# coding: utf-8

# In[20]:


import numpy as np
import pandas as pd
import scipy.stats as stats

from merton_model import merton_df
from expected_loss import el_df
from merton_model import log_returns
from portfolio_simulation import L, run_simulation, compute_credit_var
from merton_model import merton_solver, compute_dd_pd, RISK_FREE_RATE, TIME_HORIZON
from merton_model import market_caps, total_debt, sigma_vol


# In[21]:


def stress_rate_spike(merton_df, el_df, L):
    # Stress scenario: RBI emergency rate hike to 9% — increases debt servicing costs
    # Re-runs Merton solver with stressed risk free rate to compute new PDs

    stressed_r = 0.09
    stressed_merton = merton_df.copy()

    for name in merton_df.index:

        E = market_caps[name]
        sigma_E = sigma_vol[name]
        D = total_debt[name]

        V, sigma_V, ier = merton_solver(E, sigma_E, D, stressed_r, TIME_HORIZON)
        if ier != 1:
            print(f"Warning: solver did not converge for {name} (rate spike scenario)")

        DD, PD = compute_dd_pd(V, sigma_V, D, stressed_r, TIME_HORIZON)

        stressed_merton.loc[name, "PD"] = PD  # Update PD under stressed rate

    stressed_losses = run_simulation(stressed_merton, el_df, L) 
    el, var, credit_var = compute_credit_var(stressed_losses)
    return el, var, credit_var


# In[22]:


stress_rate_spike(merton_df, el_df, L)


# In[23]:


rate_el, rate_var, rate_credit_var = stress_rate_spike(merton_df, el_df, L)
print(f"Rate Spike Scenario:")
print(f"Expected Loss:   ₹{rate_el:,.0f}")
print(f"Credit VaR 99%:  ₹{rate_var:,.0f}")
print(f"Unexpected Loss: ₹{rate_credit_var:,.0f}")


# In[24]:


def stress_market_crash(merton_df, el_df, L):
    # Stress scenario: market crash — equity volatility spikes 50% across all firms
    # Higher volatility increases asset uncertainty, pushing PDs up

    stressed_merton = merton_df.copy()

    for name in merton_df.index:

        stressed_sigma_E = (sigma_vol[name]) * 1.5  # 50% volatility shock
        E = market_caps[name]
        D = total_debt[name]

        V, sigma_V, ier = merton_solver(E, stressed_sigma_E, D, RISK_FREE_RATE, TIME_HORIZON)
        if ier != 1:
            print(f"Warning: solver did not converge for {name} (market crash scenario)")

        DD, PD = compute_dd_pd(V, sigma_V, D, RISK_FREE_RATE, TIME_HORIZON)

        stressed_merton.loc[name, "PD"] = PD

    stressed_losses = run_simulation(stressed_merton, el_df, L) 
    el, var, credit_var = compute_credit_var(stressed_losses)
    return el, var, credit_var


# In[25]:


crash_el, crash_var, crash_credit_var = stress_market_crash(merton_df, el_df, L)
print(f"Market Crash Scenario:")
print(f"Expected Loss:   ₹{crash_el:,.0f}")
print(f"Credit VaR 99%:  ₹{crash_var:,.0f}")
print(f"Unexpected Loss: ₹{crash_credit_var:,.0f}")


# In[26]:


def stress_sector_collapse(merton_df, el_df, L):
    # Stress scenario: telecom/infra sector collapse
    # Vodafone Idea and Adani LGD raised to 90% — severe recovery deterioration

    stressed_el = el_df.copy()
    stressed_el.loc[["Vodafone Idea", "Adani Enterprises"], "LGD"] = 0.9  # Stressed LGD
    stressed_el["Expected Loss"] = stressed_el["PD"] * stressed_el["LGD"] * stressed_el["EAD"]  # Keep EL column consistent with stressed LGD

    stressed_losses = run_simulation(merton_df, stressed_el, L) 
    el, var, credit_var = compute_credit_var(stressed_losses)

    return el, var, credit_var


# In[27]:


sector_el, sector_var, sector_credit_var = stress_sector_collapse(merton_df, el_df, L)
print(f"Sector Collapse Scenario:")
print(f"Expected Loss:   ₹{sector_el:,.0f}")
print(f"Credit VaR 99%:  ₹{sector_var:,.0f}")
print(f"Unexpected Loss: ₹{sector_credit_var:,.0f}")


# In[28]:


baseline_losses = run_simulation(merton_df, el_df, L)
baseline_el, baseline_var, baseline_credit_var = compute_credit_var(baseline_losses)

stress_results = {
    "Baseline": (baseline_el, baseline_var, baseline_credit_var),
    "Rate Spike": (rate_el, rate_var, rate_credit_var),
    "Market Crash": (crash_el, crash_var, crash_credit_var),
    "Sector Collapse": (sector_el, sector_var, sector_credit_var)
}

stress_df = pd.DataFrame(stress_results, index=["EL", "VaR 99%", "Credit VaR"]).T
stress_df.to_csv("data/stress_results.csv")
print(stress_df)


# In[ ]:




