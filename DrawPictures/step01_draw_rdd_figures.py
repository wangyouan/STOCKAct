#!/usr/bin/env python

# -*- coding: utf-8 -*-
# @Filename: step01_draw_rdd_figures
# @Date: 2025/7/15
# @Author: Mark Wang
# @Email: wangyouan@gamil.com

import os

import pandas as pd
from pandas import DataFrame
import matplotlib.pyplot as plt

from Constants import Constants as const
from Utilities import draw_rdd_pictures

if __name__ == '__main__':
    pic_save_path = os.path.join(const.REGRESSION_RESULT_PATH, '20250715')

    if not os.path.isdir(pic_save_path):
        os.makedirs(pic_save_path)

    pc_reg_df: DataFrame = pd.read_stata(os.path.join(const.RESULT_PATH, '20250713_stock_act_spc_reg_data_v2.dta'))

    dep_var_dict = {'logGuidanceForecast': 'Log(1 + GuidanceCount)', 'coverage': 'ANALYSTS', 'cpie_gpin': 'GPIN',
                    'fcsterror_last': 'FCSTERROR', 'dispersion_last': 'DISPERSION', 'idiosyn': 'IDIOSYN',
                    'price_delay': 'DELAY', 'GuidanceForecast': 'GuidanceCount'}


    def get_real_name(key):
        if key in dep_var_dict:
            return dep_var_dict[key]

        key_list = key.split('_')
        key_info_dict = {'CGOV': 'Corporate Governance', 'EMP': 'Employee', 'ENV': 'Environment',
                         'COM': 'Community', 'DIV': 'Diversity', 'HUM': 'Human Rights', 'PRO': 'Product',
                         'con': 'Concern', 'str': 'Strength', 'score': 'Score', 'net': ''}

        return ' '.join(map(lambda x: key_info_dict[x], key_list))


    # start_point = 15
    bin_num = 5
    pc_reg_df[const.VOTE_SHARE] /= 100
    pc_reg_df[const.VOTE_SHARE] += 0.5

    for tmp_dep_var in ['logGuidanceForecast', 'coverage', 'fcsterror_last', 'dispersion_last', 'idiosyn', 'cpie_gpin',
                        'price_delay', 'GuidanceForecast']:
        for suffix in ['']:
            dep_var = '{}{}'.format(tmp_dep_var, suffix)
            ind_var = const.VOTE_SHARE
            sub_df: DataFrame = pc_reg_df[[ind_var, dep_var, const.IS_WIN, const.GVKEY, const.YEAR]].dropna(how='any')

            fig = plt.figure(figsize=(10, 5))
            ax = plt.subplot()
            ax = draw_rdd_pictures(sub_df.copy(), ind_var, dep_var, bin_num, 0.45, order=2, x_label='Percentage of Votes',
                                   y_label='{}'.format(dep_var_dict.get(tmp_dep_var)), ax=ax)
            ax.figure.savefig(os.path.join(pic_save_path, 'dep_{}.png'.format(dep_var)))
            plt.close(fig)
