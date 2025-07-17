#!/usr/bin/env python

# -*- coding: utf-8 -*-
# @Filename: step03_construct_analysts_num_fcsterror_dispersion
# @Date: 2025/7/17
# @Author: Mark Wang
# @Email: wangyouan@gamil.com

import os
import datetime

from tqdm import tqdm
import numpy as np
import pandas as pd

from Constants import Constants as const
from Utilities import print_log

if __name__ == '__main__':
    tqdm.pandas(desc='Processing')
    print_log("Start to load ibes data")
    data_path = r'D:\Users\wangy\Documents\data'
    ibes_df = pd.read_sas(os.path.join(data_path, 'ibes', "statsum_epsus.sas7bdat"), encoding='utf-8')

    ibes_df.columns = [col.lower() for col in ibes_df.columns]
    ibes_df = ibes_df[(ibes_df['fpi'] == '1')].copy()
    print_log("Loaded ibes data")

    # Construct Analysts Data
    print_log("Start to construct Analysts data")
    columns_needed = ['ticker', 'statpers', 'numest', 'fpi', 'measure']
    # 执行本地筛选逻辑，等同于 WRDS SQL 查询
    ibes_summary = ibes_df[ibes_df['measure'] == 'EPS'][[
        'ticker', 'statpers', 'numest']].copy()

    # Convert the date column to datetime format
    ibes_summary['statpers'] = pd.to_datetime(ibes_summary['statpers'])

    # Extract year and month from 'statpers'
    ibes_summary['year'] = ibes_summary['statpers'].dt.year
    ibes_summary['month'] = ibes_summary['statpers'].dt.month

    # Calculate the average number of analysts for each firm for each fiscal year
    ibes_summary[const.YEAR] = ibes_summary['statpers'].dt.to_period('Y')

    # Group by ticker and fiscal year, then calculate the average number of analysts
    analyst_coverage = ibes_summary.groupby(['ticker', const.YEAR])['numest'].mean().reset_index()

    # Rename columns
    analyst_coverage.rename(columns={'numest': 'ANALYSTS'}, inplace=True)
    print_log("Finish to construct Analysts data")

    print_log("start to construct FCSTERROR and DISPERSION Data")

    # Construct FCSTERROR and DISPERSION Data
    ibes_df = ibes_df.loc[:,
    ['ticker', 'fpi', 'statpers', 'numest', 'fpedats', 'meanest', 'stdev', 'actual']].rename(
        columns={'meanest': 'eps_mean', 'stdev': 'eps_sd', 'actual': 'eps_actual'})
    crsp_df = pd.read_csv(os.path.join(data_path, '192501_202412_crsp_stock_return.zip')).rename(
        columns={'MthPrc': 'prc'})
    crsp_df.columns = [col.lower() for col in crsp_df.columns]

    # Convert the IBES data to annual by creating a annual value and aggregating it
    ibes_df['statpers'] = pd.to_datetime(ibes_df['statpers'])
    ibes_df[const.YEAR] = ibes_df['statpers'].dt.year
    ibes_annual = ibes_df.groupby(['ticker', const.YEAR]).agg({
        'eps_mean': 'mean',
        'eps_sd': 'mean',
        'eps_actual': 'mean',
        'numest': 'mean',
    }).reset_index()

    ibes_annual2 = ibes_df.groupby(['ticker', const.YEAR]).agg({
        'eps_mean': 'last',
        'eps_sd': 'last',
        'eps_actual': 'last',
        'numest': 'last',
    }).reset_index()

    ibes_annual = ibes_annual.merge(ibes_annual2, on=['ticker', const.YEAR], how='left', suffixes=('', '_last'))

    # Convert the CRSP data to quarterly by creating a quarter value
    crsp_df['date'] = pd.to_datetime(crsp_df['MthCalDt'.lower()])
    crsp_df[const.YEAR] = crsp_df['date'].dt.year
    crsp_annual = crsp_df.groupby(['permno', const.YEAR]).last().reset_index()

    # Use the price at the end of the previous quarter as Price_lag
    crsp_annual['Price_lag'] = crsp_annual.groupby('permno')['prc'].shift(1)

    # Step 1: 加载 ibes-crsp link
    ibes_crsp_link = pd.read_sas(os.path.join(data_path, 'ibes', 'ibcrsphist.sas7bdat'), encoding='utf-8')
    ibes_crsp_link.columns = [col.lower() for col in ibes_crsp_link.columns]
    ibes_crsp_link['sdate'] = pd.to_datetime(ibes_crsp_link['sdate']).astype('datetime64[ns]')
    ibes_crsp_link['edate'] = pd.to_datetime(ibes_crsp_link['edate']).astype('datetime64[ns]')

    print_log("Start to query permno")


    def get_permno(row):
        match = ibes_crsp_link[
            (ibes_crsp_link['ticker'] == row['ticker']) &
            (ibes_crsp_link['sdate'] <= row['fyear_date']) &
            (ibes_crsp_link['edate'] >= row['fyear_date'])
            ]
        return match['permno'].values[0] if not match.empty else pd.NA

    ibes_annual['fyear_date'] = pd.to_datetime(ibes_annual[const.YEAR].astype(str) + '-01-01').astype('datetime64[ns]')
    analyst_coverage['fyear_date'] = pd.to_datetime(analyst_coverage[const.YEAR].astype(str) + '-01-01').astype(
        'datetime64[ns]')

    analyst_coverage['permno'] = analyst_coverage.progress_apply(get_permno, axis=1)
    ibes_annual['permno'] = ibes_annual.progress_apply(get_permno, axis=1)


    # Merge IBES and CRSP Link data to get permno for each IBES ticker
    ibes_linked_df = ibes_annual.copy()
    for key in ['permno', const.YEAR]:
        ibes_linked_df[key] = pd.to_numeric(ibes_linked_df[key], errors='coerce')
        crsp_annual[key] = pd.to_numeric(crsp_annual[key], errors='coerce')
        analyst_coverage[key] = pd.to_numeric(analyst_coverage[key], errors='coerce')

    # Merge IBES-linked data with CRSP quarterly data on permno and quarter
    merged_df_ann = pd.merge(ibes_linked_df, crsp_annual, on=['permno', const.YEAR], how='inner')
    merged_df_ann = merged_df_ann[merged_df_ann['Price_lag'] > 0]

    # Create DISPERSION
    # DISPERSION is calculated as the ratio of the standard deviation of EPS forecasts (eps_sd)
    # to the stock price at the end of the previous quarter (Price_lag)
    merged_df_ann['DISPERSION'] = merged_df_ann['eps_sd'] / merged_df_ann['Price_lag']
    merged_df_ann['DISPERSION_last'] = merged_df_ann['eps_sd_last'] / merged_df_ann['Price_lag']

    # Create FCSTERROR
    # FCSTERROR is calculated as the absolute value of the difference between the mean analyst EPS forecast (eps_mean)
    # and the actual EPS (eps_actual), scaled by the stock price at the end of the previous quarter (Price_lag)
    merged_df_ann['FCSTERROR'] = abs(merged_df_ann['eps_mean'] - merged_df_ann['eps_actual']) / merged_df_ann[
        'Price_lag']
    merged_df_ann['FCSTERROR_last'] = abs(merged_df_ann['eps_mean_last'] - merged_df_ann['eps_actual_last']) / \
                                      merged_df_ann['Price_lag']

    merged_df = merged_df_ann.merge(analyst_coverage, on=['permno', const.YEAR], how='left')

    duplicated_keys = [i for i in merged_df.keys() if i.endswith('_x') or i.endswith('_y')]
    print(duplicated_keys)

    merged_df.drop(duplicated_keys, axis=1).to_pickle(os.path.join(const.TEMP_PATH, '1976_2023_analysts_fd_data.pkl'))
