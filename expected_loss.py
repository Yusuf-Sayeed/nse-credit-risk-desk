import pandas as pd
import numpy as np
from merton_model import merton_df, TICKERS


NOTIONAL = 100_00_00_000

ALL_LGD = {
    "Mahindra & Mahindra" : 0.4,
    "Adani Enterprises" : 0.5,
    "Zomato" : 0.75,
    "JSW Steel" : 0.35,
    "Vodafone Idea" : 0.6,
    "DLF" : 0.3,
    "Indigo (IndiGo)" : 0.45,
    "Sun Pharma" : 0.4,
    "HDFC Bank" : 0.55,
    "Reliance Industries" : 0.35
}


def expected_loss(merton_df, lgd_dict, notional):

    # Computes Expected Loss (EL = PD × LGD × EAD) for each company in the portfolio
    # merton_df : Module 1 output containing PD per company
    # lgd_dict  : Loss Given Default assumptions by sector
    # notional  : Equal INR exposure per company

    dic = {}

    for name in merton_df.index:

        pdefault = merton_df.loc[name, "PD"]
        lgd = lgd_dict[name]
        ead = notional

        el = pdefault * lgd * ead
        dic[name] = {"PD" : pdefault, "LGD" : lgd, "EAD" : ead, "Expected Loss" : el}

    results = pd.DataFrame(dic).T
    return results


expected_loss(merton_df, ALL_LGD, NOTIONAL)


el_df = expected_loss(merton_df, ALL_LGD, NOTIONAL)
el_df.to_csv("data/expected_loss.csv")