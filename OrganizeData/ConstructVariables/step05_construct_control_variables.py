#!/usr/bin/env python

# -*- coding: utf-8 -*-
# @Filename: step05_construct_control_variables
# @Date: 2025/7/18
# @Author: Mark Wang
# @Email: wangyouan@gamil.com

import os

import wrds
import pandas as pd
import numpy as np

from Constants import Constants as const

if __name__ == '__main__':
    # 建立 WRDS 连接
    conn = wrds.Connection(wrds_username='wangyouan')

    # 下载 compustat 年度数据
    compustat = conn.raw_sql("""
                             SELECT gvkey, datadate, fyear, at, dltt, ceq, csho, prcc_f, ib, mkvalt, dlc
                             FROM comp.funda
                             WHERE indfmt = 'INDL'
                               AND datafmt = 'STD'
                               AND popsrc = 'D'
                               AND consol = 'C'
                             """)

    # 确保日期格式正确
    compustat['datadate'] = pd.to_datetime(compustat['datadate'])

    # 计算控制变量
    compustat['mkvalt'] = compustat['mkvalt'].fillna(compustat['prcc_f'] * compustat['csho'])
    compustat['size'] = compustat['mkvalt'].apply(np.log)
    compustat['lev'] = (compustat['dltt'].fillna(0) + compustat['dlc'].fillna(0)) / compustat['at']
    compustat['bm'] = compustat['ceq'] / compustat['mkvalt']
    compustat['roa'] = compustat['ib'] / compustat['at']

    # 清理极端值（可选）
    for var in ['lev', 'bm', 'roa', 'size']:
        compustat[var] = compustat[var].replace([np.inf, -np.inf], np.nan)

    # 删除缺失值（可选）
    compustat = compustat.dropna(subset=['size', 'lev', 'bm', 'roa'], how='all')

    # 保存或继续分析
    compustat.to_pickle(os.path.join(const.TEMP_PATH, '20250718_ctat_controls.pkl'))
    conn.close()
