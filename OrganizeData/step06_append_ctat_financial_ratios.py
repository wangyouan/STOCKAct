#!/usr/bin/env python

# -*- coding: utf-8 -*-
# @Filename: step06_append_ctat_financial_ratios
# @Date: 2024/8/22
# @Author: Mark Wang
# @Email: wangyouan@gamil.com

import os

import numpy as np
import pandas as pd
from pandas import DataFrame

from Constants import Constants as const

if __name__ == '__main__':
    ctat_df: DataFrame = pd.read_csv(os.path.join(const.COMPUSTAT_PATH, '2008_2016_ctat_firm_ratios.zip'))
    ctat_df['adate'] = pd.to_datetime(ctat_df['adate'], format='%Y-%m-%d')
    ctat_df[const.YEAR] = ctat_df['adate'].dt.year

    ctat_df_annual: DataFrame = ctat_df.drop_duplicates(subset=[const.GVKEY, const.YEAR], keep='last').drop(
        ['adate', 'qdate', 'public_date'], axis=1)

    # append the constructed data to regression file
    reg_df: DataFrame = pd.read_stata(os.path.join(const.RESULT_PATH, '20240821_stock_act_reg_data.dta'))
    ctat_df_annual_1: DataFrame = ctat_df_annual.copy()
    ctat_df_annual_1[const.YEAR] -= 1
    reg_df: DataFrame = reg_df.merge(ctat_df_annual, on=[const.GVKEY, const.YEAR], how='left').merge(
        ctat_df_annual_1, on=[const.GVKEY, const.YEAR], how='left', suffixes=('', '_1'))
    reg_df.to_stata(os.path.join(const.RESULT_PATH, '20240822_stock_act_reg_data_v2.dta'), write_index=False,
                    version=117)
