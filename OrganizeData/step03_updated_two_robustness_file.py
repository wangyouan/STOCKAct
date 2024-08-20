#!/usr/bin/env python

# -*- coding: utf-8 -*-
# @Filename: step03_updated_two_robustness_file
# @Date: 2024/8/20
# @Author: Mark Wang
# @Email: wangyouan@gamil.com

import os

import pandas as pd
from pandas import DataFrame
from scipy.stats.mstats import winsorize

from Constants import Constants as const

if __name__ == '__main__':
    ZGY_PATH = os.path.join(const.DATA_PATH, 'fromZGY')
    winsorize_variable_list = ['log_frequency', 'log_market_value', 'lev', 'BM', 'ROA', 'EarnVol', 'ret', 'turnover',
                               'StkVol']

    fiscal_year_df: DataFrame = pd.read_stata(os.path.join(ZGY_PATH, 'A2_RobustTime', 'robustness_fiscalyearend.dta'))
    no12_df: DataFrame = pd.read_stata(os.path.join(ZGY_PATH, 'A2_RobustTime', 'robustness_no12.dta'))

    for key in winsorize_variable_list:
        fiscal_year_df.loc[fiscal_year_df[key].notnull(), f'{key}_w'] = winsorize(fiscal_year_df[key].dropna(),
                                                                                  limits=[0.01, 0.01])
        no12_df.loc[no12_df[key].notnull(), f'{key}_w'] = winsorize(no12_df[key].dropna(), limits=[0.01, 0.01])

    fiscal_year_df.to_stata(os.path.join(const.RESULT_PATH, '20240820_stock_act_afyear.dta'), write_index=False,
                            version=117)
    no12_df.to_stata(os.path.join(const.RESULT_PATH, '20240820_stock_act_no12.dta'), write_index=False, version=117)
