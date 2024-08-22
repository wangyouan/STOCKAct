#!/usr/bin/env python

# -*- coding: utf-8 -*-
# @Filename: step05_append_some_consequence_test_variables
# @Date: 2024/8/22
# @Author: Mark Wang
# @Email: wangyouan@gamil.com

""" significant variables: STOCK_MONTHLY_STD pi_AT"""

import os

import numpy as np
import pandas as pd
from pandas import DataFrame
from scipy.stats.mstats import winsorize

from Constants import Constants as const

if __name__ == '__main__':
    # construct some variables
    ctat_df: DataFrame = pd.read_csv(os.path.join(const.COMPUSTAT_PATH, '1950_2022_ctat_all_data.zip'),
                                     usecols=['fyear', const.GVKEY, 'prcc_f', 'csho', 'mkvalt', 'ni', 'ib',
                                              'at', 'ebitda', 'pi'],
                                     dtype={const.GVKEY: int}).rename(columns={'fyear': const.YEAR}).drop_duplicates(
        subset=[const.GVKEY, const.YEAR], keep='last').sort_values(by=[const.GVKEY, const.YEAR], ascending=True)
    ctat_df.loc[:, 'prcc_f'] = ctat_df['prcc_f'].fillna(ctat_df['mkvalt'] / ctat_df['csho'])
    ctat_df.loc[:, 'lag_at'] = ctat_df.groupby([const.GVKEY])['at'].shift(1)
    ctat_df.loc[:, 'lag_prcc_f'] = ctat_df.groupby([const.GVKEY])['prcc_f'].shift(1)
    ctat_df2: DataFrame = ctat_df.loc[ctat_df[const.YEAR] > 2007].copy()

    ctat_df2['STOCK_RETURN'] = ctat_df2['prcc_f'] / ctat_df2['lag_prcc_f'] - 1
    new_keys = [const.GVKEY, const.YEAR, 'STOCK_RETURN']
    for key in ['ni', 'ib', 'pi', 'ebitda']:
        ctat_df2[f'{key}_AT'] = ctat_df2[key] / ctat_df2['at']
        ctat_df2[f'{key}_LAGAT'] = ctat_df2[key] / ctat_df2['lag_at']
        new_keys.extend([f'{key}_AT', f'{key}_LAGAT'])

    # construct stock volatility
    ctat_month_df: DataFrame = pd.read_csv(os.path.join(const.COMPUSTAT_PATH, '2008_2016_ctat_ret_monthly.zip'))
    ctat_month_df['datadate'] = pd.to_datetime(ctat_month_df['datadate'], format='%Y-%m-%d')
    ctat_month_df[const.YEAR] = ctat_month_df['datadate'].dt.year

    stock_volatility = ctat_month_df.groupby([const.GVKEY, const.YEAR])['trt1m'].std().reset_index(drop=False)
    stock_volatility.rename(columns={'trt1m': 'STOCK_MONTHLY_STD'}, inplace=True)

    # append the constructed data to regression file
    reg_df: DataFrame = pd.read_stata(os.path.join(const.RESULT_PATH, '20240821_stock_act_reg_data.dta'))

    reg_df2: DataFrame = reg_df.merge(stock_volatility, how='left', on=[const.GVKEY, const.YEAR]).merge(
        ctat_df2[new_keys], on=[const.GVKEY, const.YEAR], how='left').replace([np.inf, -np.inf], np.nan)

    stock_volatility[const.YEAR] -= 1
    ctat_df2[const.YEAR] -= 1

    reg_df2: DataFrame = reg_df2.merge(stock_volatility, how='left', on=[const.GVKEY, const.YEAR],
                                       suffixes=('', '_1')).merge(
        ctat_df2[new_keys], on=[const.GVKEY, const.YEAR], how='left', suffixes=('', '_1')).replace(
        [np.inf, -np.inf], np.nan)

    winsorize_variable_list = new_keys[2:]
    winsorize_variable_list.append('STOCK_MONTHLY_STD')
    for key in winsorize_variable_list:
        new_key = f'{key}_1'
        reg_df2.loc[reg_df2[key].notnull(), key] = winsorize(reg_df2[key].dropna(), limits=[0.01, 0.01])
        reg_df2.loc[reg_df2[new_key].notnull(), new_key] = winsorize(reg_df2[new_key].dropna(), limits=[0.01, 0.01])
        reg_df2[key] = reg_df2[key].fillna(reg_df2[new_key])
        reg_df2[new_key] = reg_df2[new_key].fillna(reg_df2[key])

    reg_df2.to_stata(os.path.join(const.RESULT_PATH, '20240822_stock_act_reg_data.dta'), write_index=False, version=117)
