#!/usr/bin/env python

# -*- coding: utf-8 -*-
# @Filename: step02_merge_all_regression_data_continue
# @Date: 2024/8/19
# @Author: Mark Wang
# @Email: wangyouan@gamil.com

import os

import pandas as pd
from pandas import DataFrame
from scipy.stats.mstats import winsorize

from Constants import Constants as const

if __name__ == '__main__':
    reg_df: DataFrame = pd.read_pickle(os.path.join(const.TEMP_PATH, '20240812_stock_act_reg_bm_hhi_lobby_prisk.pkl'))
    ZGY_PATH = os.path.join(const.DATA_PATH, 'fromZGY')

    # merge table4-5_GovernCross Not found in the code useless?
    # cross_customer_contract: DataFrame = pd.read_stata(
    #     os.path.join(ZGY_PATH, 'table4-5_GovernCross', 'cross_customer_contract.dta')).drop(['level_0'], axis=1)

    ## merge high low custom num
    cross_vol_num: DataFrame = pd.read_stata(
        os.path.join(ZGY_PATH, 'table4-5_GovernCross', 'cross_vol_num.dta')).drop(['level_0'], axis=1).rename(
        columns={'high': 'HighGovCustomNum', 'low': 'LowGovCustomNum', 'high1': 'HighGovSalesVol',
                 'low1': 'LowGovSalesVol', 'num_customer': 'GovCustomNum', 'gov_vol': 'GovSalesVol'})
    reg_df2: DataFrame = reg_df.merge(cross_vol_num.loc[:,
                                      ['gvkey', 'fiscal_year', 'HighGovCustomNum', 'GovCustomNum', 'LowGovCustomNum',
                                       'HighGovSalesVol', 'GovSalesVol', 'LowGovSalesVol']],
                                      on=['gvkey', 'fiscal_year'], how='left')

    # merge sales percentage
    sales_percentage: DataFrame = pd.read_stata(
        os.path.join(ZGY_PATH, 'table4-5_GovernCross', 'sales_percentage.dta')).rename(
        columns={'high': 'HighGovSalesRatio', 'low': 'LowGovSalesRatio'})

    reg_df3: DataFrame = reg_df2.rename(columns={'all_gov': 'MajorGovCustomer'}).merge(
        sales_percentage.loc[:, ['gvkey', 'fiscal_year', 'HighGovSalesRatio', 'LowGovSalesRatio', 'gov_annual_sales',
                                 'all_annual_sales', 'annual_per_sale', 'avg_sales_per']], on=['gvkey', 'fiscal_year'],
        how='left')

    # merge government contract
    customer_contract: DataFrame = pd.read_stata(
        os.path.join(ZGY_PATH, 'table4-5_GovernCross', 'customer_contract.dta')).rename(
        columns={'all_customer': 'hasGovContract'})
    customer_contract.loc[:, 'hasGovContract'] = (customer_contract['hasGovContract'] > 0).astype(int)
    customer_contract_filtered = customer_contract[customer_contract['fiscal_year'] < 2012]
    gvkey_with_contract = customer_contract_filtered[customer_contract_filtered['hasGovContract'] > 0]['gvkey'].unique()
    customer_contract.loc[:, 'GovContractor'] = (customer_contract['gvkey'].isin(gvkey_with_contract)).astype(int)

    reg_df4: DataFrame = reg_df3.merge(
        customer_contract.loc[:, ['gvkey', 'fiscal_year', 'hasGovContract', 'GovContractor']],
        on=['gvkey', 'fiscal_year'], how='left')
    reg_df4.loc[:, 'OnlyGovContractor'] = ((reg_df4['MajorGovCustomer'] == 0) & (reg_df4['GovContractor'] == 1)).astype(
        int)
    reg_df4.to_stata(os.path.join(const.RESULT_PATH, '20240820_temp_reg_data.dta'), write_index=False, version=117)

    # merge forcast type files
    reg_df4['gvkey'] = reg_df4['gvkey'].astype(int)
    for suffixes in ['ann', 'eps', 'noneps', 'qtr']:
        data_df: DataFrame = pd.read_stata(os.path.join(ZGY_PATH, 'table3_ForecastType', f'robustness_{suffixes}.dta'))
        reg_df4: DataFrame = reg_df4.merge(data_df.loc[:, ['gvkey', 'fiscal_year', 'frequency', 'log_frequency']],
                                           on=['gvkey', 'fiscal_year'], how='left', suffixes=('', f'_{suffixes}'))

    days_dat_df: DataFrame = pd.read_stata(os.path.join(ZGY_PATH, 'table3_ForecastType', 'robustness_day_freq.dta'))
    reg_df5: DataFrame = reg_df4.merge(days_dat_df.loc[:, ['gvkey', 'fiscal_year', 'log_frequency_day']],
                                       on=['gvkey', 'fiscal_year'], how='left')

    # merge main test precision
    precision_df: DataFrame = pd.read_stata(os.path.join(ZGY_PATH, 'A4_Precision', 'main_test_precision.dta'))
    precision_df['gvkey'] = precision_df['gvkey'].astype(int)
    precision_df['fiscal_year'] = precision_df['fiscal_year'].astype(int)
    reg_df6: DataFrame = reg_df5.merge(precision_df.loc[:, ['gvkey', 'fiscal_year', 'width']],
                                       on=['gvkey', 'fiscal_year'], how='left')

    # merge dummy for clean control firms
    cleanbenchmark: DataFrame = pd.read_stata(os.path.join(ZGY_PATH, 'A3_RobustSample', 'cleanbenchmark.dta'))
    cleanbenchmark['gvkey'] = cleanbenchmark['gvkey'].astype(int)
    cleanbenchmark['isCleanControl'] = 1
    reg_df7: DataFrame = reg_df6.merge(cleanbenchmark[['gvkey', 'fiscal_year', 'isCleanControl']],
                                       on=['gvkey', 'fiscal_year'], how='left')

    # merge dummy for covered in IBES
    robustness_nomf: DataFrame = pd.read_stata(os.path.join(ZGY_PATH, 'A3_RobustSample', 'robustness_nomf.dta'))
    robustness_nomf['isCoveredIBES'] = 1
    reg_df8: DataFrame = reg_df7.merge(robustness_nomf[['gvkey', 'fiscal_year', 'isCoveredIBES']],
                                       on=['gvkey', 'fiscal_year'], how='left')

    # construct dummy for six year sample
    reg_df8['sixYearSample'] = reg_df8['fiscal_year'].apply(lambda x: int(2008 < x < 2015))

    winsorize_variable_list = ['log_frequency', 'log_market_value', 'lev', 'BM', 'ROA', 'EarnVol', 'ret', 'turnover',
                               'StkVol', 'log_frequency_ann', 'log_frequency_eps', 'log_frequency_noneps',
                               'log_frequency_qtr', 'log_frequency_day', 'width', 'env_info', 'social_info']

    for key in winsorize_variable_list:
        reg_df8.loc[reg_df8[key].notnull(), f'{key}_w'] = winsorize(reg_df8[key].dropna(), limits=[0.01, 0.01])

    reg_df8['sic'] = reg_df8['sic'].astype(int).astype(str).str.zfill(4)
    reg_df8['sic2'] = reg_df8['sic'].str[:2]
    reg_df8.rename(columns={'treat': 'CongressOwn'}, inplace=True)
    reg_df8.to_stata(os.path.join(const.RESULT_PATH, '20240820_stock_act_reg_data.dta'), write_index=False, version=117)
