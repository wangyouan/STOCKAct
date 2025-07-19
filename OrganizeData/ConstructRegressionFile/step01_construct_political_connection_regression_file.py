#!/usr/bin/env python

# -*- coding: utf-8 -*-
# @Filename: step01_construct_political_connection_regression_file
# @Date: 2025/7/18
# @Author: Mark Wang
# @Email: wangyouan@gamil.com

import os

import numpy as np
import pandas as pd
from scipy.stats.mstats import winsorize

from Constants import Constants as const

if __name__ == '__main__':
    # load dependent variables
    dep_df = pd.read_pickle(os.path.join(const.TEMP_PATH, '20250718_temp_dependent_variables.pkl'))
    ccm_path = r'D:\Users\wangy\Documents\data\ccm'

    ccm_df = pd.read_sas(os.path.join(os.path.join(ccm_path, 'ccm_lookup.sas7bdat')), encoding='utf-8')

    # merge dep with gvkeys
    # 标准化列名
    dep_df.columns = dep_df.columns.str.lower()
    ccm_df.columns = ccm_df.columns.str.lower()

    # 保留需要的字段
    ccm_sub = ccm_df[['gvkey', 'lpermno', 'year1', 'year2']].copy()

    # 为提高 merge 效率，先 merge on permno，再做年份筛选
    merged = pd.merge(dep_df, ccm_sub, left_on='permno', right_on='lpermno', how='left')

    # 年份条件筛选：fiscal_year ∈ [year1, year2]
    matched = merged[
        (merged['fiscal_year'] >= merged['year1']) &
        (merged['fiscal_year'] <= merged['year2'])
        ].copy()

    # 如果多个匹配，选择最近的 year1（可选）
    matched = matched.sort_values(by=['permno', 'fiscal_year', 'year1'], ascending=[True, True, False])
    matched = matched.drop_duplicates(subset=['permno', 'fiscal_year'], keep='first')

    # 删除辅助列（可选）
    matched = matched.drop(columns=['lpermno', 'year1', 'year2'])
    matched[const.GVKEY] = matched[const.GVKEY].astype(int)

    # load political connection database
    pc_df = pd.read_stata(os.path.join(const.DATA_PATH,
                                       '20190217_FEC_general_firm_year_interaction_newly_without_duplicates_interactions3.dta'))
    pc_df = pc_df[['CSTAT_gvkey', 'year', 'FEC_LoseP', 'FEC_WonP', 'FEC_TotalP']].rename(
        columns={'CSTAT_gvkey': const.GVKEY, 'year': const.YEAR, 'FEC_LoseP': 'LoseP', 'FEC_WonP': 'WinP',
                 'FEC_TotalP': 'TotalP'})
    pc_df.loc[:, 'NumP'] = pc_df['WinP'] + pc_df['LoseP']
    pc_df['WinRatio'] = pc_df['WinP'] / pc_df['NumP']

    spc_df = pd.read_stata(
        os.path.join(const.DATA_PATH, '20180829_FEC_federal_special_firm_year_candidate_merged_data.dta'))
    useful_col = 'year FEC_margin FEC_is_win CSTAT_gvkey'.split(' ')
    spc_df = spc_df[useful_col].rename(columns={'year': const.YEAR, 'CSTAT_gvkey': const.GVKEY})

    pc_reg_df = pc_df.merge(matched, on=[const.GVKEY, const.YEAR], how='left')
    spc_reg_df = spc_df.merge(matched, on=[const.GVKEY, const.YEAR], how='left')

    matched[const.YEAR] -= 1
    pc_reg_df = pc_reg_df.merge(matched, on=[const.GVKEY, const.YEAR], how='left', suffixes=('', '_1'))
    spc_reg_df = spc_reg_df.merge(matched, on=[const.GVKEY, const.YEAR], how='left', suffixes=('', '_1'))

    for key in ['numest', 'numest_last', 'guidancecount']:
        for suffix in ['', '_1']:
            target_key = key + suffix
            min_year_pc = pc_reg_df.loc[pc_reg_df[target_key].notnull(), const.YEAR].min()
            min_year_spc = spc_reg_df.loc[pc_reg_df[target_key].notnull(), const.YEAR].min()

            fillna_index_pc = pc_reg_df[pc_reg_df[const.YEAR] >= min_year_pc].index
            fillna_index_spc = spc_reg_df[spc_reg_df[const.YEAR] >= min_year_spc].index

            pc_reg_df.loc[fillna_index_pc, target_key] = pc_reg_df.loc[fillna_index_pc, target_key].fillna(0)
            spc_reg_df.loc[fillna_index_spc, target_key] = spc_reg_df.loc[fillna_index_spc, target_key].fillna(0)

    pc_reg_df.loc[:, 'lnguidancecount'] = pc_reg_df['guidancecount'].apply(np.log1p)
    pc_reg_df.loc[:, 'lnguidancecount_1'] = pc_reg_df['guidancecount_1'].apply(np.log1p)
    spc_reg_df.loc[:, 'lnguidancecount_1'] = spc_reg_df['guidancecount_1'].apply(np.log1p)
    spc_reg_df.loc[:, 'lnguidancecount'] = spc_reg_df['guidancecount'].apply(np.log1p)

    ctrl_df = pd.read_pickle(os.path.join(const.TEMP_PATH, '20250718_ctat_controls.pkl')).rename(
        columns={'fyear': const.YEAR})
    ctrl_df[const.GVKEY] = ctrl_df[const.GVKEY].astype(int)

    # 清理极端值（可选）
    for var in ['lev', 'bm', 'roa', 'size']:
        ctrl_df[var] = ctrl_df[var].replace([np.inf, -np.inf], np.nan)

    pc_reg_df = pc_reg_df.merge(ctrl_df, on=[const.GVKEY, const.YEAR], how='left')
    spc_reg_df = spc_reg_df.merge(ctrl_df, on=[const.GVKEY, const.YEAR], how='left')

    common_keys = list(set(pc_reg_df.keys()).intersection(spc_reg_df.keys()))
    pc_reg_df = pc_reg_df.replace([np.inf, -np.inf], np.nan)
    spc_reg_df = spc_reg_df.replace([np.inf, -np.inf], np.nan)

    for column in common_keys:
        if column in {const.GVKEY, const.YEAR, 'sic', 'datadate'}:
            continue

        non_na_data = pc_reg_df[column].dropna().astype(np.float64)
        winsorized_data = winsorize(non_na_data, limits=(0.01, 0.01))
        pc_reg_df.loc[non_na_data.index, column] = winsorized_data

        non_na_data = spc_reg_df[column].dropna().astype(np.float64)
        winsorized_data = winsorize(non_na_data, limits=(0.01, 0.01))
        spc_reg_df.loc[non_na_data.index, column] = winsorized_data

    pc_reg_df = pc_reg_df.drop_duplicates(subset=[const.GVKEY, const.YEAR], keep='first').dropna(
        subset=[const.GVKEY, const.YEAR], how='any')
    spc_reg_df = spc_reg_df.drop_duplicates(subset=[const.GVKEY, const.YEAR], keep='first').dropna(
        subset=[const.GVKEY, const.YEAR], how='any')
    spc_reg_df['int_term'] = spc_reg_df['FEC_margin'] * spc_reg_df['FEC_is_win']
    spc_reg_df['margin2'] = spc_reg_df['FEC_margin'] * spc_reg_df['FEC_margin']
    spc_reg_df['int_term2'] = spc_reg_df['margin2'] * spc_reg_df['FEC_is_win']

    pc_reg_df.to_stata(os.path.join(const.RESULT_PATH, '20250719_pc_reg_data.dta'), write_index=False)
    spc_reg_df.to_stata(os.path.join(const.RESULT_PATH, '20250719_spc_reg_data.dta'), write_index=False)
