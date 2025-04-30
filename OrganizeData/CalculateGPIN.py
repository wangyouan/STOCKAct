#!/usr/bin/env python

# -*- coding: utf-8 -*-
# @Filename: CalculateGPIN
# @Date: 2025/4/30
# @Author: Mark Wang
# @Email: wangyouan@gamil.com

## Source: https://edwinhu.github.io/pin/


import os
import datetime

import numpy as np
from scipy.special import gammaln
import pandas as pd
from numpy import log, exp
import wrds
from pandas import DataFrame

try:
    from itertools import imap
except ImportError:
    imap = map

# optimization
from numba import jit


def lfact(x):
    """Compute the log factorial using the scipy gammaln function.

    This is commonly referred to as Stirlings approximation/formula for factorials."""
    return gammaln(x + 1)


def nanexp(x):
    """Computes the exponential of x, and replaces nan and inf with finite numbers.

    Returns an array or scalar replacing Not a Number (NaN) with zero, (positive) infinity with a very large number and negative infinity with a very small (or negative) number."""
    return np.nan_to_num(np.exp(x))

# GPIN method
def _lf_gpin(th_b, th_s, r, p, n_buys, n_sells, pdenom=1):
    res = log(th_b) * n_buys + log(1 - th_s) * n_sells - lfact(n_buys) - lfact(n_sells) - gammaln(r) + log(
        1 - p) * r + log(p) * (n_buys + n_sells) + gammaln(r + n_buys + n_sells) - log(pdenom) * r - log(pdenom) * (
                  n_buys + n_sells)
    return res


def _ll_gpin(a, r, p, eta, d, th, n_buys, n_sells):
    return np.array([log(1 - a) + _lf_gpin(th, th, r, p, n_buys, n_sells),
                     log(a * d) + _lf_gpin(th + eta, th, r, p, n_buys, n_sells, 1 + eta * p),
                     log(a * (1 - d)) + _lf_gpin(th, th - eta, r, p, n_buys, n_sells, 1 + eta * p)])


def compute_alpha_gpin(a, r, p, eta, d, th, n_buys, n_sells):
    """Compute the conditional alpha given parameters, buys, and sells.

    """
    ys = _ll_gpin(a, r, p, eta, d, th, n_buys, n_sells)

    ymax = ys.max(axis=0)
    lik = exp(ys - ymax)
    alpha = lik[1:].sum(axis=0) / lik.sum(axis=0)

    return alpha


# Example usage to download data from WRDS TAQ database using WRDS package
def download_taq_data(start_year, end_year):
    """Downloads required data from WRDS TAQ database for calculating r_d, r_o, and y_e.

    Params
    ------
    start_year : int
        The starting year for the data download.
    end_year : int
        The ending year for the data download.

    Returns
    -------
    DataFrame
        A DataFrame containing the data needed to calculate r_d, r_o, and y_e.
    """
    db = wrds.Connection(wrds_username='aheitz')
    data_list = []

    for year in range(start_year, end_year + 1):
        query = f"""
        SELECT date, sym_root, sym_suffix, buynumtrades_lr, sellnumtrades_lr, oprc, cprc, ret_mkt_m,
               vw_price_m, mid_after_open, total_vol_m, total_vol_b, total_vol_a
        FROM taqmsec.wrds_iid_{year}
        WHERE sym_root IS NOT NULL
        """
        yearly_data = db.raw_sql(query)
        data_list.append(yearly_data)

    db.close()
    taq_data = pd.concat(data_list, ignore_index=True)
    return taq_data

if __name__ == '__main__':
    # prepare taq data
    taq_data = download_taq_data(2010, 2019)

    taq_data['y_e'] = (taq_data['buynumtrades_lr'] - taq_data['sellnumtrades_lr']) / (
                taq_data['buynumtrades_lr'] + taq_data['sellnumtrades_lr'])
    taq_data['r_d'] = (taq_data['vw_price_m'] - taq_data['mid_after_open'] + taq_data.get('divamt', 0)) / taq_data[
        'mid_after_open']
    taq_data['r_o'] = (taq_data['mid_after_open'] - taq_data['vw_price_m']) / taq_data['mid_after_open']

    # Load GPIN parameters
    gpin_parameter_df: DataFrame = pd.read_csv('gpin-1319.csv').drop(['f', 'rc'],
                                                                                                    axis=1).rename(
        columns={'yyyy': 'year'})
    gpin_parameter_df2: DataFrame = pd.read_csv('gpin_yearly.csv').rename(
        columns={'yyyy': 'year'})
    gpin_parameter_df: DataFrame = pd.concat([gpin_parameter_df, gpin_parameter_df2], ignore_index=True)

    # Download tad crsp linkage file
    db = wrds.Connection(wrds_username='aheitz')
    query = f"""
    SELECT date, permno, sym_suffix, sym_root
    FROM wrdsapps_link_crsp_taqm.taqmclink
    WHERE sym_root IS NOT NULL AND date between '2013-01-01' and '2019-12-31'
    """
    taq_crsp_link = db.raw_sql(query)
    db.close()

    taq_data_crsp = taq_data.drop(['sym_suffix'], axis=1).drop_duplicates(
        subset=['date', 'sym_root'], keep='first').merge(
        taq_crsp_link.dropna(subset=['permno']).drop(['sym_suffix'], axis=1).drop_duplicates(
            subset=['date', 'sym_root'], keep='first'), on=['date', 'sym_root'], how='left')

    taq_data_crsp['permno'] = taq_data_crsp.groupby(['sym_root'])['permno'].bfill()
    taq_data_crsp['permno'] = taq_data_crsp.groupby(['sym_root'])['permno'].ffill()
    taq_data_crsp.dropna(subset=['permno'], inplace=True)

    taq_data_crsp['date'] = pd.to_datetime(taq_data['date'])
    taq_data_crsp['year'] = taq_data_crsp['date'].dt.year
    taq_data_crsp['permno'] = pd.to_numeric(taq_data_crsp['permno'], errors='coerce')
    taq_data_crsp_model = taq_data_crsp.merge(gpin_parameter_df, on=['permno', 'year'], how='left').replace(
        {'NA': np.nan})

    taq_data_crsp_model.dropna(subset=['a', 'd', 'eta', 'p', 'r', 'th', 'buynumtrades_lr'], how='any', inplace=True)

    taq_data_crsp_model.loc[:, 'gpin'] = taq_data_crsp_model.apply(
        lambda x: compute_alpha_gpin(x['a'], x['r'], x['p'], x['eta'], x['d'], x['th'], x['buynumtrades_lr'],
                                     x['sellnumtrades_lr']), axis=1)

    taq_data_crsp_model.to_csv('daily_gpin.csv', index=False)
