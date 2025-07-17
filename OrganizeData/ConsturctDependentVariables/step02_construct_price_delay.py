#!/usr/bin/env python

# -*- coding: utf-8 -*-
# @Filename: step02_construct_price_delay
# @Date: 2025/7/17
# @Author: Mark Wang
# @Email: wangyouan@gamil.com

"""
Hou, K., & Moskowitz, T. J. (2005). Market Frictions, Price Delay, and the Cross-Section of Expected Returns. The
Review of Financial Studies, 18(3), 981–1020. https://doi.org/10.1093/rfs/hhi023
"""

import os
import warnings
import datetime

import pandas as pd
import numpy as np
import statsmodels.api as sm
from tqdm import tqdm

from Constants import Constants as const

warnings.simplefilter("ignore", category=RuntimeWarning)


def process_firm_year(group: pd.DataFrame, permno: int, year: int) -> dict:
    """对单个 firm-year 数据进行回归并计算 price delay"""
    group = group.sort_values('DlyCalDt').reset_index(drop=True)

    for lag in range(1, 5):
        group[f'vwretd_lag{lag}'] = group['vwretd'].shift(lag)

    group = group.dropna()
    if len(group) < 10:
        return None

    y = group['DlyRet'].values
    X_full = sm.add_constant(group[['vwretd', 'vwretd_lag1', 'vwretd_lag2', 'vwretd_lag3', 'vwretd_lag4']].values)
    X_restricted = sm.add_constant(group[['vwretd']].values)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        model_full = sm.OLS(y, X_full).fit()
        model_restricted = sm.OLS(y, X_restricted).fit()

    r2_full = model_full.rsquared
    r2_restricted = model_restricted.rsquared
    delay = 1 - r2_restricted / r2_full if r2_full > 0 else np.nan

    return {
        'PERMNO': permno,
        'year': year,
        'price_delay': delay,
        'r2_full': r2_full,
        'r2_restricted': r2_restricted,
        'n_obs': len(group)
    }


# -------------------- Step 2: 对某个文件计算 price_delay -------------------- #
def compute_price_delay_from_file(filepath: str) -> pd.DataFrame:
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now}] Processing file: {os.path.basename(filepath)}")

    df = pd.read_csv(filepath, dtype={'DlyCalDt': str})
    df['DlyCalDt'] = pd.to_datetime(df['DlyCalDt'])
    df = df.sort_values(['PERMNO', 'DlyCalDt'])
    df['DlyRet'] = pd.to_numeric(df['DlyRet'], errors='coerce')
    df['vwretd'] = pd.to_numeric(df['vwretd'], errors='coerce')
    df = df.dropna(subset=['DlyRet', 'vwretd'])

    weekly = (
        df.set_index('DlyCalDt')
        .groupby('PERMNO')[['DlyRet', 'vwretd']]
        .resample('W-FRI')
        .apply(lambda x: (1 + x).prod() - 1)
        .dropna()
        .reset_index()
    )
    weekly['year'] = weekly['DlyCalDt'].dt.year

    results = []
    grouped = weekly.groupby(['PERMNO', 'year'])
    for (permno, year), group in tqdm(grouped, desc="Firm-year regression"):
        result = process_firm_year(group, permno, year)
        if result is not None:
            results.append(result)

    return pd.DataFrame(results)


# -------------------- Step 3: 批量处理多个文件并合并 -------------------- #
def batch_process_crsp_folder(folder_path: str) -> pd.DataFrame:
    all_results = []

    # 获取所有 .zip 或 .csv 文件
    files = [f for f in os.listdir(folder_path) if f.endswith('.zip') or f.endswith('.csv')]
    files.sort()  # 可选：按文件名排序处理

    for file in files:
        if os.path.isfile(os.path.join(const.TEMP_PATH, file.replace('zip', 'pkl'))):
            df_result = pd.read_pickle(os.path.join(const.TEMP_PATH, file.replace('zip', 'pkl')))
        else:
            file_path = os.path.join(folder_path, file)
            df_result = compute_price_delay_from_file(file_path)
            df_result.to_pickle(os.path.join(const.TEMP_PATH, file.replace('zip', 'pkl')))

        all_results.append(df_result)

    # 合并所有 price_delay_df
    combined_df = pd.concat(all_results, ignore_index=True)
    return combined_df

if __name__ == '__main__':
    # -------------------- Step 4: 执行 -------------------- #
    data_path = r'D:\Users\wangy\Documents\data\crsp'
    price_delay_all = batch_process_crsp_folder(data_path)

    # 可选：保存
    price_delay_all.to_pickle(os.path.join(const.TEMP_PATH, "hm2005_all_price_delay.pkl"))
