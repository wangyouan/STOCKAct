#!/usr/bin/env python

# -*- coding: utf-8 -*-
# @Filename: step04_append_unregulated_file
# @Date: 2024/8/21
# @Author: Mark Wang
# @Email: wangyouan@gamil.com

import os

import pandas as pd
from pandas import DataFrame

from Constants import Constants as const

if __name__ == '__main__':
    reg_df: DataFrame = pd.read_stata(os.path.join(const.RESULT_PATH, '20240820_stock_act_reg_data.dta'))
    reg_df.rename(columns={'lobby_high': 'donation_high', 'amount': 'donation_amount'}, inplace=True)

    ZGY_PATH = os.path.join(const.DATA_PATH, 'fromZGY')
    unregulated_df: DataFrame = pd.read_stata(os.path.join(ZGY_PATH, 'A3_RobustSample', 'unregulated.dta'))

    unregulated_df['unregulated'] = 1
    reg_df2: DataFrame = reg_df.merge(unregulated_df[['unregulated', 'gvkey', 'fiscal_year']],
                                      on=['gvkey', 'fiscal_year'], how='left')

    reg_df2.to_stata(os.path.join(const.RESULT_PATH, '20240821_stock_act_reg_data.dta'), write_index=False, version=117)
