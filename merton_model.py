#!/usr/bin/env python
# coding: utf-8

# In[57]:


import numpy as np
import pandas as pd
import yfinance as yf
import scipy.stats as stats
import scipy.optimize as opt
import os


# In[58]:


TICKERS = {
    "M&M.NS" : "Mahindra & Mahindra",
    "ADANIENT.NS" : "Adani Enterprises",
    "ETERNAL.NS" : "Zomato",
    "JSWSTEEL.NS" : "JSW Steel",
    "IDEA.NS" : "Vodafone Idea",
    "DLF.NS" : "DLF",
    "INDIGO.NS" : "Indigo (IndiGo)",
    "SUNPHARMA.NS" : "Sun Pharma",
    "HDFCBANK.NS" : "HDFC Bank",
    "RELIANCE.NS" : "Reliance Industries"
}

WEIGHTS = np.full(10, 0.1) # Reserved for future portfolio weighting

START = "2024-06-01"
END = "2026-06-01"

RISK_FREE_RATE = 0.065
TIME_HORIZON = 1


# In[59]:


def fetch_prices(tickers, start_date, end_date):

    raw_data = yf.download(list(tickers.keys()), start_date, end_date, progress = False)

    prices = raw_data.Close.copy()
    prices.columns = [TICKERS[t] for t in prices.columns]
    prices.dropna(how = "all", inplace = True)

    print(f"Downloaded {len(prices)} Trading Days")

    return prices


# In[60]:


prices = fetch_prices(TICKERS, START, END)
prices = prices.ffill()


# In[61]:


def compute_log_returns(prices):

    log_returns = np.log(prices / prices.shift(1)).dropna(how = "all")

    return log_returns


# In[62]:


log_returns = compute_log_returns(prices)


# In[63]:


def compute_equity_volatility(log_returns):

    returns_std = log_returns.std()
    annualized_vol = returns_std * np.sqrt(252)

    return annualized_vol.sort_values()


# In[64]:


sigma_vol = compute_equity_volatility(log_returns)


# In[65]:


def fetch_market_cap(tickers):

    market_cap = {}
    for t, name in tickers.items():
        mcap = yf.Ticker(t).info["marketCap"]
        if mcap is None:
            print(f"Warning: marketCap missing for {name} ({t})")
        market_cap[name] = mcap

    return pd.Series(market_cap)


# In[66]:


market_caps = fetch_market_cap(TICKERS)
market_caps


# In[67]:


def fetch_total_debt(tickers):

    total_debt = {}
    for t, name in tickers.items():
        debt = yf.Ticker(t).info["totalDebt"]
        if debt is None:
            print(f"Warning: totalDebt missing for {name} ({t})")
        total_debt[name] = debt 

    return pd.Series(total_debt)


# In[68]:


total_debt = fetch_total_debt(TICKERS)
total_debt


# In[69]:


def merton_solver(E, sigma_E, D, r, T):
    # E       : Equity value (market capitalization of the firm)
    # sigma_E : Equity volatility (annualized std of log returns)
    # D       : Face value of debt (total borrowings from balance sheet)
    # r       : Risk free rate (Indian 10Y G-Sec yield)
    # T       : Time horizon in years (1 year standard)

    def equations(vars):

        V, sigma_V = vars # V = asset value, sigma_V = asset volatility (both unobservable)

        d1 = (np.log(V / D) + (r + 0.5 * sigma_V**2) * T) / (sigma_V * np.sqrt(T))
        d2 = d1 - sigma_V * np.sqrt(T)

        # Equation 1: Black-Scholes — equity is a call option on firm assets
        # Residual should be zero when V and sigma_V are correct
        eq1 = E - (V * stats.norm.cdf(d1) - D * np.exp(-r * T) * stats.norm.cdf(d2))

        # Equation 2: Ito's Lemma, links equity volatility to asset volatility
        # Residual should be zero when V and sigma_V are correct
        eq2 = sigma_E * E - stats.norm.cdf(d1) * sigma_V * V

        return [eq1, eq2]

    V0 = E + D
    sigma_V0 = sigma_E * E / (E + D)

    # fsolve iteratively adjusts V and sigma_V until both equations equal zero
    result = opt.fsolve(equations, [V0, sigma_V0], full_output = True)
    V, sigma_V = result[0]
    ier = result[2]  # 1 = converged successfully

    return V, sigma_V, ier


# In[70]:


def compute_dd_pd(V, sigma_V, D, r, T):

    # Note: uses r - 0.5*sigma_V² (real world drift, not risk neutral like d1)
    DD = (np.log(V / D) + (r - 0.5 * sigma_V**2) * T) / (sigma_V * np.sqrt(T))

    # N(-DD) gives the left tail probability — the chance of defaulting
    PD = stats.norm.cdf(-DD)

    return DD, PD


# In[71]:


results = {}

for t, name in TICKERS.items():
    sigma_E = sigma_vol.loc[name]
    E = market_caps.loc[name]
    D = total_debt.loc[name]

    V, sigma_V, ier = merton_solver(E, sigma_E, D, RISK_FREE_RATE, TIME_HORIZON)

    if ier != 1:
        print(f"Warning: solver did not converge for {name}")

    DD, PD = compute_dd_pd(V, sigma_V, D, RISK_FREE_RATE, TIME_HORIZON)

    results[name] = {"V": V, "sigma_V": sigma_V, "DD": DD, "PD": PD}

merton_df = pd.DataFrame(results).T
merton_df


# In[72]:


os.makedirs("data", exist_ok=True)
merton_df.to_csv("data/merton_results.csv")

