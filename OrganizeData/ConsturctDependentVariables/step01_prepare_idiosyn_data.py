#!/usr/bin/env python

# -*- coding: utf-8 -*-
# @Filename: step01_prepare_idiosyn_data
# @Date: 2025/7/17
# @Author: Mark Wang
# @Email: wangyouan@gamil.com

"""
Hutton, A. P., Marcus, A. J., & Tehranian, H. (2009). Opaque Financial Reports, R2, and Crash Risk. Journal of Financial
Economics, 94(1), 67–86. https://doi.org/10.1016/j.jfineco.2008.10.003
"""

import os

from tqdm import tqdm
import pandas as pd
import numpy as np
import statsmodels.api as sm

from Constants import Constants as const
from Utilities import get_fama_french_industry


def calculate_monthly_synchrony(group, mkt_only=False, ind_only=False):
    dep_var = 'RET'
    if mkt_only:
        if ind_only:
            raise ValueError('Only one of mkt_only and ind_only should be True')
        ind_vars = ['rm_t-1', 'vwretd', 'rm_t+1']
        suffix = '_MKT'
    elif ind_only:
        ind_vars = ['ri_t-1', 'Industry_Return', 'ri_t+1']
        suffix = '_IND'
    else:
        ind_vars = ['rm_t-1', 'ri_t-1', 'vwretd', 'Industry_Return', 'rm_t+1', 'ri_t+1']
        suffix = ''

    # Shift the independent variables to match the lag/lead structure as per equation (4)
    group['rm_t-1'] = group['vwretd'].shift(1)
    group['ri_t-1'] = group['Industry_Return'].shift(1)
    group['rm_t+1'] = group['vwretd'].shift(-1)
    group['ri_t+1'] = group['Industry_Return'].shift(-1)

    all_vars = [dep_var]
    all_vars.extend(ind_vars)

    # Drop rows with NaN values after shifting
    group = group.dropna(subset=all_vars, how='any')

    # Define the dependent and independent variables
    y = group[dep_var]
    X = group[ind_vars]
    X = sm.add_constant(X)  # Add a constant term to the regression

    try:
        # Run the regression
        model = sm.OLS(y, X, missing='drop').fit()
        r_squared = model.rsquared

        # Calculate IDIOSYN and SYNCHRONICITY
        idiosyn = -1 * np.log(r_squared / (1 - r_squared)) if r_squared < 1 else np.nan

    except Exception as e:
        # If regression fails for any reason, return NaN
        idiosyn = np.nan

    return pd.Series({f'IDIOSYN{suffix}': idiosyn})


if __name__ == '__main__':
    tqdm.pandas(desc='Calculating IDIOSYN')

    data_path = r'D:\Users\wangy\Documents\data'

    # Load the CRSP data
    data = pd.read_csv(os.path.join(data_path, '192012_202412_crsp_stock_return.zip'))

    # Convert date to datetime and sort by PERMNO and date
    data['date'] = pd.to_datetime(data['date'])
    data = data.sort_values(by=['PERMNO', 'date'], ascending=True)
    data['month'] = data['date'].dt.to_period('M')

    # Load the Fama-French industry classification data
    industry_returns = pd.read_csv(os.path.join(data_path, '48_Industry_Portfolios_Daily.csv'))
    industry_returns['Date'] = pd.to_datetime(industry_returns['Date'], format='%Y%m%d')

    data['HSICCD'].replace('Z', np.nan, inplace=True)
    data['HSICCD'] = data['HSICCD'].fillna(data['SICCD'].replace('Z', np.nan))
    data = data[data['HSICCD'].notnull()]
    data['HSICCD'] = data['HSICCD'].astype(int)

    # Apply the mapping to the CRSP data
    data['fama_french_industry'] = data['HSICCD'].apply(get_fama_french_industry)

    # Prepare the market and industry return variables
    # Assuming 'vwretd' is the value-weighted market return and industry_returns contains daily industry returns
    industry_returns = industry_returns.melt(id_vars=['Date'], var_name='Industry', value_name='Industry_Return')
    industry_returns['Date'] = pd.to_datetime(industry_returns['Date'])

    # Convert industry returns to monthly level
    industry_returns['month'] = industry_returns['Date'].dt.to_period('M')
    industry_monthly_returns = industry_returns.groupby(['Industry', 'month'])['Industry_Return'].progress_apply(
        lambda x: (1 + x).prod() - 1).reset_index()

    # Convert market returns to weekly level
    data['vwretd'] = pd.to_numeric(data['vwretd'], errors='coerce')
    data['RET'] = pd.to_numeric(data['RET'], errors='coerce')

    # Merge CRSP data with weekly industry returns
    data = pd.merge(data, industry_monthly_returns, left_on=['month', 'fama_french_industry'],
                    right_on=['month', 'Industry'], how='left')

    # Drop rows with NaN values in relevant columns
    data = data.dropna(subset=['RET', 'vwretd', 'Industry_Return'])

    firm_monthly_data = data[
        ['PERMNO', 'month', 'date', 'RET', 'vwretd', 'Industry_Return']].drop_duplicates(
        subset=['PERMNO', 'month'], keep='last')

    firm_monthly_data['year'] = firm_monthly_data['date'].dt.year
    idiosyn = firm_monthly_data.groupby(['PERMNO', 'year']).progress_apply(calculate_monthly_synchrony).reset_index()
    idiosyn.to_pickle(os.path.join(const.TEMP_PATH, '20250717_idiosyn_monthly.pkl'))

