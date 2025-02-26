#!/usr/bin/env python

# -*- coding: utf-8 -*-
# @Filename: step07_append_some_cost_of_capital_data
# @Date: 2024/8/24
# @Author: Mark Wang
# @Email: wangyouan@gamil.com

"""We calculate the ICC measure as a mean value of the ICCs derived from the GLS model (Gebhardt,
Lee, and Swaminathan 2001), the OJM model (Ohlson and Juettner-Nauroth 2005) the CAT model (Claus and Thomas 2001),
and the PEG model (Easton 2004). The GLS and CAT models are based on variants
of the residual-income model, and they differ in terms of their forecasting horizon and terminal value
estimation. The PEG and OJM models are based on the abnormal-growth-in-earnings model, they differ in
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

    # # sort percerived coc data
    # coc_df: DataFrame = pd.read_stata(
    #     os.path.join(const.DATABASE_PATH, 'Cost of Capital', 'perceived cost of capital',
    #                  'CoCdata_V2_0_Posted11012024.dta'))
    #
    # coc_ann_df: DataFrame = coc_df.groupby([const.GVKEY, 'year'])[
    #     ['predicted_costcap', 'predicted_hurdle']].mean().reset_index(drop=False).rename(columns={'year': const.YEAR})
    # coc_ann_df[const.GVKEY] = coc_ann_df[const.GVKEY].astype(int)

    # append coc data to regression data
    reg_df: DataFrame = pd.read_stata(os.path.join(const.RESULT_PATH, '20250226_stock_act_data_v1.dta'))
    # reg_df2: DataFrame = reg_df.merge(lee_merged_df, on=[const.GVKEY, const.YEAR], how='left')

    for lag_year in range(1, 5):
        tmp_df: DataFrame = lee_merged_df.copy()
        lee_merged_df.loc[:, const.YEAR] -= lag_year
        reg_df = reg_df.merge(tmp_df, on=[const.GVKEY, const.YEAR], how='left', suffixes=('', f'_{lag_year}'))
    # reg_df2: DataFrame = reg_df.merge(lee_merged_df, on=[const.GVKEY, const.YEAR], how='left').merge(
    #     coc_ann_df, on=[const.GVKEY, const.YEAR], how='left')
    # lee_merged_df[const.YEAR] -= 1
    # coc_ann_df[const.YEAR] -= 1
    # reg_df3: DataFrame = reg_df2.merge(lee_merged_df, on=[const.GVKEY, const.YEAR], how='left',
    #                                    suffixes=('', '_1')).merge(coc_ann_df, on=[const.GVKEY, const.YEAR], how='left',
    #                                                               suffixes=('', '_1'))

    # fillna_keys = ['GLS_mech_annual', 'OJM_mech_annual', 'CAT_mech_annual', 'PEG_mech_annual']
    #
    # for key in fillna_keys:
    #     match_suffixes = ['an_annual', 'mech_f_annual', 'an_f_annual', 'mech_month', 'mech_f_month', 'an_f_month']
    #     for suffix in match_suffixes:
    #         fillna_key = key.replace('mech_annual', suffix)
    #         reg_df2[key] = reg_df2[key].fillna(reg_df2[fillna_key])
    #
    # key = 'CCC_annual'
    # match_keys = ['CCC_f_annual', 'CCC_month', 'CCC_f_month']
    # for match_key in match_keys:
    #     reg_df2[key] = reg_df2[key].fillna(reg_df2[match_key])
    #
    # missing_keys = ['GLS_mech_annual', 'OJM_mech_annual', 'CAT_mech_annual', 'PEG_mech_annual', 'CCC_annual']
    # for key in missing_keys:
    #     for i in reg_df2.loc[reg_df2[key].isnull()].index:
    #         gvkey = reg_df2.loc[i, const.GVKEY]
    #         year = reg_df2.loc[i, const.YEAR]
    #         target_df = lee_merged_df.loc[(lee_merged_df[const.GVKEY] == gvkey)]
    #         if not target_df.empty:
    #             reg_df2.loc[i, key] = target_df[key].mean()
    #
    # key = 'OJM_mech_annual'
    # missing_index = reg_df2[reg_df2[key].isnull() & reg_df2['CCC_annual'].notnull()].index
    # for i in missing_index:
    #     reg_df2.loc[i, key] = reg_df2.loc[i, 'CCC_annual'] * 4 - reg_df2.loc[i, 'GLS_mech_annual'] - reg_df2.loc[
    #         i, 'CAT_mech_annual'] - reg_df2.loc[i, 'PEG_mech_annual']

    reg_df.to_stata(os.path.join(const.RESULT_PATH, '20250226_stock_act_data_v2.dta'), write_index=False,
                    version=119)
