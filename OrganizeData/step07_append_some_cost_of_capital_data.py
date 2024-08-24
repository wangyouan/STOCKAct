#!/usr/bin/env python

# -*- coding: utf-8 -*-
# @Filename: step07_append_some_cost_of_capital_data
# @Date: 2024/8/24
# @Author: Mark Wang
# @Email: wangyouan@gamil.com

"""We calculate the ICC measure as a mean value of the ICCs derived from the GLS model (Gebhardt,
Lee, and Swaminathan 2001), the CAT model (Claus and Thomas 2001), the PEG model (Easton 2004),
and the AGR model (Ohlson and Juettner-Nauroth 2005). The GLS and CAT models are based on variants
of the residual-income model, and they differ in terms of their forecasting horizon and terminal value
estimation. The PEG and AGR models are based on the abnormal-growth-in-earnings model, they differ in
their formulation of the long-term growth in abnormal earnings. For details on the computations, see Lee,
So, and Wang (2021)’s Appendix B.2. All four ICC measures are based on earnings forecasts derived from
the cross-sectional mechanical forecast model of Hou, Van Dijk, and Zhang (2012), and do not have to rely
on analyst forecasts, which facilitates the ICC computation for a large cross-section of international firms.

from Do Investors Care About Biodiversity? page 28
"""

import os

import numpy as np
import pandas as pd
from pandas import DataFrame
from scipy.stats.mstats import winsorize

from Constants import Constants as const

if __name__ == '__main__':
    # sort original lee's data
    lee_merged_df = DataFrame()
    for file_name in ['erp_public_240107', 'erp_public_annual_240107']:
        lee_df: DataFrame = pd.read_csv(
            os.path.join(const.DATABASE_PATH, 'Cost of Capital', f'{file_name}.zip')).drop(['permno'], axis=1)
        lee_df['yearmonth'] = pd.to_datetime(lee_df['yearmonth'], format='%Y%m')
        lee_df[const.YEAR] = lee_df['yearmonth'].dt.year

        lee_df_year_mean = lee_df.drop(['yearmonth'], axis=1).groupby([const.GVKEY, const.YEAR]).mean().reset_index(
            drop=False)
        lee_df[const.YEAR] = lee_df['yearmonth'].apply(lambda x: int(x.year) if x.month > 4 else x.year - 1)
        lee_df_fyear_mean = lee_df.drop(['yearmonth'], axis=1).groupby([const.GVKEY, const.YEAR]).mean().reset_index(
            drop=False)
        lee_annual_df: DataFrame = lee_df_year_mean.merge(lee_df_fyear_mean, on=[const.GVKEY, const.YEAR], how='outer',
                                                          suffixes=('', '_f'))
        if lee_merged_df.empty:
            lee_merged_df = lee_annual_df.copy()
        else:
            lee_merged_df: DataFrame = lee_merged_df.merge(lee_annual_df, on=[const.GVKEY, const.YEAR], how='outer',
                                                           suffixes=('_month', '_annual'))

    # sort percerived coc data
    coc_df: DataFrame = pd.read_stata(
        os.path.join(const.DATABASE_PATH, 'perceived cost of capital', 'CoCdata_V2_0_Posted11012024.dta'))

    coc_ann_df: DataFrame = coc_df.groupby([const.GVKEY, 'year'])[
        ['predicted_costcap', 'predicted_hurdle']].mean().reset_index(drop=False).rename(columns={'year': const.YEAR})
    coc_ann_df[const.GVKEY] = coc_ann_df[const.GVKEY].astype(int)

    # append coc data to regression data
    reg_df: DataFrame = pd.read_stata(os.path.join(const.RESULT_PATH, '20240821_stock_act_reg_data.dta'))
    reg_df2: DataFrame = reg_df.merge(lee_merged_df, on=[const.GVKEY, const.YEAR], how='left').merge(
        coc_ann_df, on=[const.GVKEY, const.YEAR], how='left')
    lee_merged_df[const.YEAR] -= 1
    coc_ann_df[const.YEAR] -= 1
    reg_df3: DataFrame = reg_df2.merge(lee_merged_df, on=[const.GVKEY, const.YEAR], how='left',
                                       suffixes=('', '_1')).merge(coc_ann_df, on=[const.GVKEY, const.YEAR], how='left',
                                                                  suffixes=('', '_1'))
    key_list = [i for i in coc_ann_df.keys() if i not in {const.GVKEY, const.YEAR}]
    key_list.extend([i for i in lee_merged_df.keys() if i not in {const.GVKEY, const.YEAR}])
    for key in key_list:
        new_key = f'{key}_1'
        reg_df3[key] = reg_df3[key].fillna(reg_df3[new_key])
        reg_df3[new_key] = reg_df3[new_key].fillna(reg_df3[key])
        if reg_df3[key].notnull().sum() == 0:
            continue
        reg_df3.loc[reg_df3[key].notnull(), key] = winsorize(reg_df3[key].dropna(), limits=[0.01, 0.01])
        reg_df3.loc[reg_df3[new_key].notnull(), new_key] = winsorize(reg_df3[new_key].dropna(), limits=[0.01, 0.01])
    reg_df3.to_stata(os.path.join(const.RESULT_PATH, '20240824_stock_act_reg_data.dta'), write_index=False, version=117)