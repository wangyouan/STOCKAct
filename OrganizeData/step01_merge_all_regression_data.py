#!/usr/bin/env python

# -*- coding: utf-8 -*-
# @Filename: step01_merge_all_regression_data
# @Date: 2024/8/12
# @Author: Mark Wang
# @Email: wangyouan@gamil.com

import os

import pandas as pd
from pandas import DataFrame

from Constants import Constants as const

if __name__ == '__main__':
    ZGY_PATH = os.path.join(const.DATA_PATH, 'fromZGY')
    main_reg_df: DataFrame = pd.read_stata(
        os.path.join(ZGY_PATH, 'table1289A5_MainAddition', 'main_test_result_esg_polihold.dta'))

    main_reg_df.loc[:, 'social_info'] = main_reg_df['social_x'] + main_reg_df['social_y']
    main_reg_df.loc[:, 'env_info'] = main_reg_df['per_enviro_all_year'] * 100
    main_reg_df.loc[:, 'sic'] = main_reg_df['sic_x']

    drop_keys = [i for i in main_reg_df.keys() if i.endswith('_x') or i.endswith('_y') or i.startswith('per_')]
    drop_keys.append('BM')
    reg_df: DataFrame = main_reg_df.drop(drop_keys, axis=1)

    # Fix BM construction problem
    ctat_df: DataFrame = pd.read_csv(os.path.join(const.COMPUSTAT_PATH, '1950_2022_ctat_all_data.zip'),
                                     usecols=['fyear', const.GVKEY, 'bkvlps', 'prcc_f', 'csho', 'mkvalt'],
                                     dtype={const.GVKEY: str}).rename(columns={'fyear': const.YEAR})
    ctat_df.loc[:, 'prcc_f'] = ctat_df['prcc_f'].fillna(ctat_df['mkvalt'] / ctat_df['csho'])
    ctat_df.loc[:, 'BM'] = ctat_df['bkvlps'] / ctat_df['prcc_f']

    reg_df_bm: DataFrame = reg_df.merge(
        ctat_df.loc[:, [const.GVKEY, const.YEAR, 'BM']].dropna(how='any').drop_duplicates(
            subset=[const.GVKEY, const.YEAR], keep='last'), on=[const.GVKEY, const.YEAR],
        how='left')

    ## fill in some missing bm ratio
    bm_key_dict = {4210: 0.814652576,
                   4211: 0.674317369,
                   4229: 0.858208208,
                   4230: 0.549231262,
                   4231: 0.712084718,
                   4502: 0.635028865,
                   4503: 0.763307633,
                   8986: 0.581212121,
                   9635: 0.501158961,
                   11383: 0.41515873,
                   11528: 0.26318113
                   }
    for index in bm_key_dict:
        reg_df_bm.loc[index, 'BM'] = bm_key_dict[index]

    # merge hhi information
    t7_high_df: DataFrame = pd.read_stata(os.path.join(ZGY_PATH, 'table7_HHICross', 'high_hhisale_sample.dta'))
    t7_low_df: DataFrame = pd.read_stata(os.path.join(ZGY_PATH, 'table7_HHICross', 'low_hhisale_sample.dta'))
    t7_high_df['HHI_high'] = 1
    t7_low_df['HHI_high'] = 0
    hhi_df: DataFrame = pd.concat([t7_high_df, t7_low_df], axis=0)
    reg_df_bm['gvkey'] = reg_df_bm['gvkey'].astype(int)

    reg_df_hhi: DataFrame = reg_df_bm.merge(hhi_df.loc[:, ['gvkey', 'fiscal_year', 'HHI', 'HHI_high']],
                                            on=['gvkey', 'fiscal_year'], how='left')

    # merge lobby information
    t6_lobby_high: DataFrame = pd.read_stata(os.path.join(ZGY_PATH, 'table6_PoliCross', 'high_lobby_sample.dta'))
    t6_lobby_low: DataFrame = pd.read_stata(os.path.join(ZGY_PATH, 'table6_PoliCross', 'low_lobby_sample.dta'))
    t6_lobby_high['lobby_high'] = 1
    t6_lobby_low['lobby_high'] = 0
    lobby_df: DataFrame = pd.concat([t6_lobby_high, t6_lobby_low], axis=0)
    reg_df_lobby: DataFrame = reg_df_hhi.merge(lobby_df.loc[:, ['gvkey', 'fiscal_year', 'amount', 'lobby_high']],
                                               on=['gvkey', 'fiscal_year'], how='left')

    # merge prisk information
    t6_prisk_high: DataFrame = pd.read_stata(os.path.join(ZGY_PATH, 'table6_PoliCross', 'high_prisk_sample.dta'))
    t6_prisk_low: DataFrame = pd.read_stata(os.path.join(ZGY_PATH, 'table6_PoliCross', 'low_prisk_sample.dta'))
    t6_prisk_high['prisk_high'] = 1
    t6_prisk_low['prisk_high'] = 0
    prisk_df: DataFrame = pd.concat([t6_prisk_high, t6_prisk_low], axis=0)
    reg_df_prisk: DataFrame = reg_df_lobby.merge(
        prisk_df.loc[:, ['gvkey', 'fiscal_year', 'PRisk', 'PSentiment', 'prisk_high']],
        on=['gvkey', 'fiscal_year'], how='left')

    reg_df_prisk.to_pickle(os.path.join(const.TEMP_PATH, '20240812_stock_act_reg_bm_hhi_lobby_prisk.pkl'))
