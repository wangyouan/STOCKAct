#!/usr/bin/env python

# -*- coding: utf-8 -*-
# @Filename: step02_append_textual_data
# @Date: 2025/7/19
# @Author: Mark Wang
# @Email: wangyouan@gamil.com

import os

import pandas as pd
from tqdm import tqdm

from Constants import Constants as const

if __name__ == '__main__':
    ta_df = pd.read_stata(os.path.join(const.DATA_PATH, 'all_year_govreg.dta')).rename(
        columns={'tic': 'ticker', 'year': const.YEAR})
    ta_df[const.YEAR] = ta_df[const.YEAR].astype(int)

    # Step 3: 加载 IBES-CRSP Link
    data_path = r'D:\Users\wangy\Documents\data'
    ibes_crsp_link = pd.read_sas(os.path.join(data_path, 'ibes', 'ibcrsphist.sas7bdat'), encoding='utf-8').dropna(
        subset=['PERMNO'])
    ibes_crsp_link.columns = [col.lower() for col in ibes_crsp_link.columns]
    ibes_crsp_link['sdate'] = pd.to_datetime(ibes_crsp_link['sdate'])
    ibes_crsp_link['edate'] = pd.to_datetime(ibes_crsp_link['edate'])
    ta_df['fyear_date'] = pd.to_datetime(ta_df[const.YEAR].astype(str) + '-01-01')

    # 强制ticker为str类型，避免数据类型混乱
    ibes_crsp_link['ticker'] = ibes_crsp_link['ticker'].astype(str)
    ta_df['ticker'] = ta_df['ticker'].astype(str)

    # Step 4: 添加 PERMNO
    tqdm.pandas(desc="Matching PERMNO")

    def get_permno(row):
        match = ibes_crsp_link[
            (ibes_crsp_link['ticker'] == row['ticker']) &
            (ibes_crsp_link['sdate'] <= row['fyear_date']) &
            (ibes_crsp_link['edate'] >= row['fyear_date'])
        ]
        return int(match['permno'].values[0]) if not match.empty else pd.NA

    ta_df['permno'] = ta_df.progress_apply(get_permno, axis=1)
    ta_df['permno'] = pd.to_numeric(ta_df['permno'], errors='coerce')
    ta_df.dropna(how='any', inplace=True)

    pc_df = pd.read_stata(os.path.join(const.RESULT_PATH, '20250719_stock_act_pc_reg_data_v5.dta'))
    spc_df = pd.read_stata(os.path.join(const.RESULT_PATH, '20250719_stock_act_spc_reg_data_v4.dta'))

    pc_df = pc_df.merge(ta_df, on=['permno', const.YEAR], how='left')
    spc_df = spc_df.merge(ta_df, on=['permno', const.YEAR], how='left')

    ta_df[const.YEAR] -= 1

    pc_df = pc_df.merge(ta_df, on=['permno', const.YEAR], how='left', suffixes=('', '_1'))
    spc_df = spc_df.merge(ta_df, on=['permno', const.YEAR], how='left', suffixes=('', '_1'))

    pc_df.to_stata(os.path.join(const.RESULT_PATH, '20250719_stock_act_pc_reg_data_v6.dta'), write_index=False)
    spc_df.to_stata(os.path.join(const.RESULT_PATH, '20250719_stock_act_spc_reg_data_v5.dta'), write_index=False)
