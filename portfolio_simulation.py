import numpy as np
import pandas as pd
import scipy.stats as stats
from merton_model import merton_df
from expected_loss import el_df
from merton_model import log_returns


def compute_correlation_matrix(log_returns):

    corr_martix = log_returns.corr()

    # Pearson correlation of daily log returns — proxy for asset return correlations

    return corr_martix


correlation_matrix = compute_correlation_matrix(log_returns)


def cholesky_decomposition(correlation_matrix):

    # Decomposes correlation matrix into L such that L @ L.T = correlation matrix

    L = np.linalg.cholesky(correlation_matrix)

    # Used to inject correlation structure into independent random draws

    return L


L = cholesky_decomposition(correlation_matrix)


def run_simulation(merton_df, el_df, L, n_simulations = 10000):

    n_companies = len(merton_df)
    thresholds = stats.norm.ppf(merton_df["PD"].values)    # Convert PD to normal distribution threshold — company defaults if shock falls below this
    lgd_values = el_df.loc[merton_df.index, "LGD"].values  # Loss Given Default per company
    ead_values = el_df.loc[merton_df.index, "EAD"].values  # Exposure at Default per company

    portfolio_losses = [] # Stores total portfolio loss for each simulation

    np.random.seed(42)
    for i in range(n_simulations):

        z = np.random.standard_normal(n_companies)        # Independent standard normal shocks, one per company
        correlated_z = L @ z                              # Introduce correlation using Cholesky matrix

        defaults = correlated_z < thresholds # Company defaults if correlated shock falls below its default threshold

        scenario_loss = (defaults * lgd_values * ead_values).sum() # Sum losses across all defaulted companies in this scenario
        portfolio_losses.append(scenario_loss)

    return np.array(portfolio_losses)


portfolio_losses = run_simulation(merton_df, el_df, L)
print(f"Simulations run: {len(portfolio_losses)}")
print(f"Mean Loss: {portfolio_losses.mean():,.2f}")
print(f"Max Loss: {portfolio_losses.max():,.2f}")


def compute_credit_var(portfolio_losses, confidence = 0.99):

    # Average portfolio loss across all simulations
    exp_losses = portfolio_losses.mean()

    # 99th percentile loss — worst case in 1 out of 100 scenarios
    var = np.percentile(portfolio_losses, confidence * 100)

    # Unexpected loss — excess above what was already priced in via EL
    credit_var = var - exp_losses

    return exp_losses, var, credit_var


compute_credit_var(portfolio_losses, confidence = 0.99)


el, var, credit_var = compute_credit_var(portfolio_losses)
print(f"Expected Loss:  ₹{el:,.0f}")
print(f"Credit VaR 99%: ₹{var:,.0f}")
print(f"Unexpected Loss: ₹{credit_var:,.0f}")


np.save("data/portfolio_losses.npy", portfolio_losses)