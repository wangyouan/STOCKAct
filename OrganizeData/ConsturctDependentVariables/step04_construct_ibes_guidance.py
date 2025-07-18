#!/usr/bin/env python

# -*- coding: utf-8 -*-
# @Filename: step04_construct_ibes_guidance
# @Date: 2025/7/18
# @Author: Mark Wang
# @Email: wangyouan@gamil.com

import os

import pandas as pd
from tqdm import tqdm

from Constants import Constants as const
from Utilities import print_log

if __name__ == '__main__':
    # 配置路径
    data_path = r'D:\Users\wangy\Documents\data'

    print_log("Start to load data")

    # Step 1: 加载 IBES Guidance 数据
    ibes_guidance_path = os.path.join(data_path, 'ibes', 'det_guidance.sas7bdat')
    guidance_df = pd.read_sas(ibes_guidance_path, encoding='utf-8')
    guidance_df.columns = guidance_df.columns.str.lower()

    print_log("Data loaded successfully")

    print_log("Start to construct dependent variables")
    # Step 2: 构建 fiscal year 并计算 guidance count 和 range forecast
    guidance_df[const.YEAR] = guidance_df['prd_yr'].astype(int)

    # guidance count (每个公司每年的guidance记录条数)
    guidance_count_df = (
        guidance_df.groupby(['ticker', const.YEAR])
        .size()
        .reset_index(name='guidancecount')
    )

    # range forecast (每条记录 guidance range 的均值)
    total_guidance = guidance_df.groupby(['ticker', const.YEAR]).size().reset_index(name='guidancecount')
    range_guidance = (
        guidance_df[guidance_df['val_1'].notna() & guidance_df['val_2'].notna()]
        .groupby(['ticker', const.YEAR])
        .size()
        .reset_index(name='range_count')
    )

    # 合并并计算比例
    ibes_annual = pd.merge(total_guidance, range_guidance, on=['ticker', const.YEAR], how='left')
    ibes_annual['rangeforecast'] = ibes_annual['range_count'] / ibes_annual['guidancecount']
    ibes_annual.drop(columns='range_count', inplace=True)

    print_log("Start to match PERMNO")

    # Step 3: 加载 IBES-CRSP Link
    ibes_crsp_link = pd.read_sas(os.path.join(data_path, 'ibes', 'ibcrsphist.sas7bdat'), encoding='utf-8')
    ibes_crsp_link.columns = [col.lower() for col in ibes_crsp_link.columns]
    ibes_crsp_link['sdate'] = pd.to_datetime(ibes_crsp_link['sdate'])
    ibes_crsp_link['edate'] = pd.to_datetime(ibes_crsp_link['edate'])
    ibes_annual['fyear_date'] = pd.to_datetime(ibes_annual[const.YEAR].astype(str) + '-01-01')

    # 强制ticker为str类型，避免数据类型混乱
    ibes_crsp_link['ticker'] = ibes_crsp_link['ticker'].astype(str)
    ibes_annual['ticker'] = ibes_annual['ticker'].astype(str)

    # Step 4: 添加 PERMNO
    tqdm.pandas(desc="Matching PERMNO")

    def get_permno(row):
        match = ibes_crsp_link[
            (ibes_crsp_link['ticker'] == row['ticker']) &
            (ibes_crsp_link['sdate'] <= row['fyear_date']) &
            (ibes_crsp_link['edate'] >= row['fyear_date'])
        ]
        return match['permno'].values[0] if not match.empty else pd.NA

    ibes_annual['permno'] = ibes_annual.progress_apply(get_permno, axis=1)

    # Step 5: 整理输出最终数据 (firm-year level with permno, guidancecount and rangeforecast)
    final_output = ibes_annual[['permno', const.YEAR, 'guidancecount', 'rangeforecast']].dropna(subset=['permno'])

    # 可选：保存结果
    output_path = os.path.join(const.TEMP_PATH, '20250718_ibes_firm_year_guidance.pkl')
    final_output.to_pickle(output_path)

    print(f"Finished! Output saved to {output_path}")
