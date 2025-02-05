#!/usr/bin/env python

# -*- coding: utf-8 -*-
# @Filename: CalculateSync
# @Date: 2025/2/5
# @Author: Mark Wang
# @Email: wangyouan@gamil.com

import os

import wrds
import pandas as pd
import numpy as np
import statsmodels.api as sm


def get_fama_french_industry(sic_code):
    if 100 <= sic_code <= 199:
        return 'Agric'
    elif 200 <= sic_code <= 299:
        return 'Food'
    elif 700 <= sic_code <= 799:
        return 'Soda'
    elif 2000 <= sic_code <= 2099:
        return 'Beer'
    elif 2100 <= sic_code <= 2199:
        return 'Smoke'
    elif 2200 <= sic_code <= 2299:
        return 'Toys'
    elif 2300 <= sic_code <= 2399:
        return 'Fun'
    elif 2700 <= sic_code <= 2749:
        return 'Books'
    elif 2500 <= sic_code <= 2519:
        return 'Hshld'
    elif 2300 <= sic_code <= 2399:
        return 'Clths'
    elif 2830 <= sic_code <= 2839:
        return 'Hlth'
    elif 3840 <= sic_code <= 3859:
        return 'MedEq'
    elif 2800 <= sic_code <= 2829:
        return 'Drugs'
    elif 2840 <= sic_code <= 2899:
        return 'Chems'
    elif 3030 <= sic_code <= 3089:
        return 'Rubbr'
    elif 2200 <= sic_code <= 2299:
        return 'Txtls'
    elif 3200 <= sic_code <= 3299:
        return 'BldMt'
    elif 1500 <= sic_code <= 1799:
        return 'Cnstr'
    elif 3300 <= sic_code <= 3399:
        return 'Steel'
    elif 3400 <= sic_code <= 3499:
        return 'FabPr'
    elif 3500 <= sic_code <= 3599:
        return 'Mach'
    elif 3600 <= sic_code <= 3699:
        return 'ElcEq'
    elif 3700 <= sic_code <= 3799:
        return 'Autos'
    elif 3720 <= sic_code <= 3729:
        return 'Aero'
    elif 3730 <= sic_code <= 3739:
        return 'Ships'
    elif 3760 <= sic_code <= 3769:
        return 'Guns'
    elif 1040 <= sic_code <= 1049:
        return 'Gold'
    elif 1000 <= sic_code <= 1099:
        return 'Mines'
    elif 1200 <= sic_code <= 1299:
        return 'Coal'
    elif 1300 <= sic_code <= 1399:
        return 'Oil'
    elif 4900 <= sic_code <= 4999:
        return 'Util'
    elif 4810 <= sic_code <= 4829:
        return 'Telcm'
    elif 7200 <= sic_code <= 7299:
        return 'PerSv'
    elif 7300 <= sic_code <= 7399:
        return 'BusSv'
    elif 3570 <= sic_code <= 3579:
        return 'Comps'
    elif 3670 <= sic_code <= 3679:
        return 'Chips'
    elif 3820 <= sic_code <= 3829:
        return 'LabEq'
    elif 2600 <= sic_code <= 2699:
        return 'Paper'
    elif 2440 <= sic_code <= 2449:
        return 'Boxes'
    elif 4000 <= sic_code <= 4799:
        return 'Trans'
    elif 5000 <= sic_code <= 5199:
        return 'Whlsl'
    elif 5200 <= sic_code <= 5999:
        return 'Rtail'
    elif 5800 <= sic_code <= 5899:
        return 'Meals'
    elif 6000 <= sic_code <= 6999:
        return 'Banks'
    elif 6300 <= sic_code <= 6399:
        return 'Insur'
    elif 6500 <= sic_code <= 6599:
        return 'RlEst'
    elif 6700 <= sic_code <= 6799:
        return 'Fin'
    else:
        return 'Other'


def calculate_synchrony(group):
    # Shift the independent variables to match the lag/lead structure as per equation (4)
    group['rm_t-1'] = group['weekly_market_return'].shift(1)
    group['ri_t-1'] = group['Industry_Return'].shift(1)
    group['rm_t+1'] = group['weekly_market_return'].shift(-1)
    group['ri_t+1'] = group['Industry_Return'].shift(-1)

    # Drop rows with NaN values after shifting
    group = group.dropna(
        subset=['weekly_return', 'rm_t-1', 'ri_t-1', 'weekly_market_return', 'Industry_Return', 'rm_t+1', 'ri_t+1'])

    # Define the dependent and independent variables
    y = group['weekly_return']
    X = group[['rm_t-1', 'ri_t-1', 'weekly_market_return', 'Industry_Return', 'rm_t+1', 'ri_t+1']]
    X = sm.add_constant(X)  # Add a constant term to the regression

    try:
        # Run the regression
        model = sm.OLS(y, X, missing='drop').fit()
        r_squared = model.rsquared

        # Calculate IDIOSYN and SYNCHRONICITY
        idiosyn = np.log((1 - r_squared) / r_squared) if r_squared < 1 else np.nan
        synchrony = -idiosyn if idiosyn is not np.nan else np.nan

    except Exception as e:
        # If regression fails for any reason, return NaN
        synchrony = np.nan

    return pd.Series({'SYNCHRONICITY': synchrony})


def calculate_synchrony_mkt(group):
    # Shift the independent variables to match the lag/lead structure as per equation (4)
    group['rm_t-1'] = group['weekly_market_return'].shift(1)
    group['rm_t+1'] = group['weekly_market_return'].shift(-1)

    # Drop rows with NaN values after shifting
    group = group.dropna(subset=['weekly_return', 'rm_t-1', 'weekly_market_return', 'rm_t+1'])

    # Define the dependent and independent variables
    y = group['weekly_return']
    X = group[['rm_t-1', 'weekly_market_return', 'rm_t+1']]
    X = sm.add_constant(X)  # Add a constant term to the regression

    try:
        # Run the regression
        model = sm.OLS(y, X, missing='drop').fit()
        r_squared = model.rsquared

        # Calculate IDIOSYN and SYNCHRONICITY
        idiosyn = np.log((1 - r_squared) / r_squared) if r_squared < 1 else np.nan
        synchrony = -idiosyn if idiosyn is not np.nan else np.nan

    except Exception as e:
        # If regression fails for any reason, return NaN
        synchrony = np.nan

    return pd.Series({'SYNCHRONICITY_MKT': synchrony})


def calculate_synchrony_ind(group):
    # Shift the independent variables to match the lag/lead structure as per equation (4)
    group['ri_t-1'] = group['Industry_Return'].shift(1)
    group['ri_t+1'] = group['Industry_Return'].shift(-1)

    # Drop rows with NaN values after shifting
    group = group.dropna(subset=['weekly_return', 'ri_t-1', 'Industry_Return', 'ri_t+1'])

    # Define the dependent and independent variables
    y = group['weekly_return']
    X = group[['ri_t-1', 'Industry_Return', 'ri_t+1']]
    X = sm.add_constant(X)  # Add a constant term to the regression

    try:
        # Run the regression
        model = sm.OLS(y, X, missing='drop').fit()
        r_squared = model.rsquared

        # Calculate IDIOSYN and SYNCHRONICITY
        idiosyn = np.log((1 - r_squared) / r_squared) if r_squared < 1 else np.nan
        synchrony = -idiosyn if idiosyn is not np.nan else np.nan

    except Exception as e:
        # If regression fails for any reason, return NaN
        synchrony = np.nan

    return pd.Series({'SYNCHRONICITY_IND': synchrony})


if __name__ == '__main__':
    # Connect to WRDS
    conn = wrds.Connection()

    data_path = r'D:\Users\wangy\Documents\data'

    # Load the CRSP data (CRSP daily data)
    data = pd.read_csv(os.path.join(data_path, '20070101_20161231_crsp_stock_return.zip'))

    # Convert date to datetime and sort by PERMNO and date
    data['date'] = pd.to_datetime(data['date'])
    data = data.sort_values(by=['PERMNO', 'date'])

    # Load the Fama-French industry classification data
    industry_returns = pd.read_csv(os.path.join(data_path, '48_Industry_Portfolios_Daily.csv'))
    industry_returns['Date'] = pd.to_datetime(industry_returns['Date'], format='%Y%m%d')

    data['HSICCD'].replace('Z', np.nan, inplace=True)
    data['HSICCD'] = data['HSICCD'].fillna(data['SICCD'].replace('Z', np.nan))
    data = data[data['HSICCD'].notnull()]
    data['HSICCD'] = data['HSICCD'].astype(int)

    # Apply the mapping to the CRSP data
    data['fama_french_industry'] = data['HSICCD'].apply(get_fama_french_industry)

    # Convert daily returns to weekly returns (assuming 'RET' is the daily return)
    data['RET'] = pd.to_numeric(data['RET'], errors='coerce')
    data['week'] = data['date'].dt.to_period('W')
    weekly_returns = data.groupby(['PERMNO', 'week'])['RET'].apply(lambda x: (1 + x).prod() - 1).reset_index()
    weekly_returns.rename(columns={'RET': 'weekly_return'}, inplace=True)

    # Merge weekly returns back with original data
    data = pd.merge(data, weekly_returns, on=['PERMNO', 'week'], how='left')

    # Drop rows with NaN weekly returns
    data = data.dropna(subset=['weekly_return'])

    # Prepare the market and industry return variables
    # Assuming 'vwretd' is the value-weighted market return and industry_returns contains daily industry returns
    industry_returns = industry_returns.melt(id_vars=['Date'], var_name='Industry', value_name='Industry_Return')
    industry_returns['Date'] = pd.to_datetime(industry_returns['Date'])

    # Convert industry returns to weekly level
    industry_returns['week'] = industry_returns['Date'].dt.to_period('W')
    industry_weekly_returns = industry_returns.groupby(['Industry', 'week'])['Industry_Return'].apply(
        lambda x: (1 + x).prod() - 1).reset_index()

    # Convert market returns to weekly level
    data['vwretd'] = pd.to_numeric(data['vwretd'], errors='coerce')
    market_return = data[['vwretd', 'week', 'date']].drop_duplicates().sort_values(by='date', ascending=True)
    weekly_market_returns = market_return.groupby('week')['vwretd'].apply(lambda x: (1 + x).prod() - 1).reset_index()
    weekly_market_returns.rename(columns={'vwretd': 'weekly_market_return'}, inplace=True)

    # Merge weekly market returns back with original data
    data = pd.merge(data, weekly_market_returns, on='week', how='left')

    # Merge CRSP data with weekly industry returns
    data = pd.merge(data, industry_weekly_returns, left_on=['week', 'fama_french_industry'],
                    right_on=['week', 'Industry'], how='left')

    # Drop rows with NaN values in relevant columns
    data = data.dropna(subset=['weekly_return', 'weekly_market_return', 'Industry_Return'])

    firm_week_data = data[
        ['PERMNO', 'week', 'date', 'weekly_return', 'weekly_market_return', 'Industry_Return']].drop_duplicates(
        subset=['PERMNO', 'week'], keep='last')

    # Create firm-year level data
    firm_week_data['year'] = firm_week_data['date'].dt.year

    synchrony = firm_week_data.groupby(['PERMNO', 'year']).apply(calculate_synchrony).reset_index()
    synchrony_ind = firm_week_data.groupby(['PERMNO', 'year']).apply(calculate_synchrony_ind).reset_index()
    synchrony_mkt = firm_week_data.groupby(['PERMNO', 'year']).apply(calculate_synchrony_mkt).reset_index()
    synchrony_df = synchrony.merge(synchrony_mkt, on=['PERMNO', 'year'], how='left').merge(
        synchrony_ind, on=['PERMNO', 'year'], how='left')

    link_file = data[['PERMNO', 'TICKER']].drop_duplicates(subset=['PERMNO'])
    synchrony_df_ticker = synchrony_df.merge(link_file, on=['PERMNO'], how='left')
    synchrony_df_ticker.to_pickle('20241006_synchrony_weekly.pkl')

