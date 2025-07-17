#!/usr/bin/env python

# -*- coding: utf-8 -*-
# @Filename: __init__.py
# @Date: 2024/10/9
# @Author: Mark Wang
# @Email: wangyouan@gamil.com


import numpy as np
from pandas import DataFrame
import matplotlib.pyplot as plt
import seaborn as sns
import datetime

from Constants import Constants as const


def get_fama_french_industry(sic_code):
    if 100 <= sic_code <= 199:
        return 'Agric'
    elif 200 <= sic_code <= 299:
        return 'Food'
    elif 700 <= sic_code <= 799:
        return 'Soda'
    elif 2000 <= sic_code <= 2099:
        return 'Beer'
    elif 2100 <= sic_code <= 2199:
        return 'Smoke'
    elif 2200 <= sic_code <= 2299:
        return 'Toys'
    elif 2300 <= sic_code <= 2399:
        return 'Fun'
    elif 2700 <= sic_code <= 2749:
        return 'Books'
    elif 2500 <= sic_code <= 2519:
        return 'Hshld'
    elif 2300 <= sic_code <= 2399:
        return 'Clths'
    elif 2830 <= sic_code <= 2839:
        return 'Hlth'
    elif 3840 <= sic_code <= 3859:
        return 'MedEq'
    elif 2800 <= sic_code <= 2829:
        return 'Drugs'
    elif 2840 <= sic_code <= 2899:
        return 'Chems'
    elif 3030 <= sic_code <= 3089:
        return 'Rubbr'
    elif 2200 <= sic_code <= 2299:
        return 'Txtls'
    elif 3200 <= sic_code <= 3299:
        return 'BldMt'
    elif 1500 <= sic_code <= 1799:
        return 'Cnstr'
    elif 3300 <= sic_code <= 3399:
        return 'Steel'
    elif 3400 <= sic_code <= 3499:
        return 'FabPr'
    elif 3500 <= sic_code <= 3599:
        return 'Mach'
    elif 3600 <= sic_code <= 3699:
        return 'ElcEq'
    elif 3700 <= sic_code <= 3799:
        return 'Autos'
    elif 3720 <= sic_code <= 3729:
        return 'Aero'
    elif 3730 <= sic_code <= 3739:
        return 'Ships'
    elif 3760 <= sic_code <= 3769:
        return 'Guns'
    elif 1040 <= sic_code <= 1049:
        return 'Gold'
    elif 1000 <= sic_code <= 1099:
        return 'Mines'
    elif 1200 <= sic_code <= 1299:
        return 'Coal'
    elif 1300 <= sic_code <= 1399:
        return 'Oil'
    elif 4900 <= sic_code <= 4999:
        return 'Util'
    elif 4810 <= sic_code <= 4829:
        return 'Telcm'
    elif 7200 <= sic_code <= 7299:
        return 'PerSv'
    elif 7300 <= sic_code <= 7399:
        return 'BusSv'
    elif 3570 <= sic_code <= 3579:
        return 'Comps'
    elif 3670 <= sic_code <= 3679:
        return 'Chips'
    elif 3820 <= sic_code <= 3829:
        return 'LabEq'
    elif 2600 <= sic_code <= 2699:
        return 'Paper'
    elif 2440 <= sic_code <= 2449:
        return 'Boxes'
    elif 4000 <= sic_code <= 4799:
        return 'Trans'
    elif 5000 <= sic_code <= 5199:
        return 'Whlsl'
    elif 5200 <= sic_code <= 5999:
        return 'Rtail'
    elif 5800 <= sic_code <= 5899:
        return 'Meals'
    elif 6000 <= sic_code <= 6999:
        return 'Banks'
    elif 6300 <= sic_code <= 6399:
        return 'Insur'
    elif 6500 <= sic_code <= 6599:
        return 'RlEst'
    elif 6700 <= sic_code <= 6799:
        return 'Fin'
    else:
        return 'Other'


def evenly_separate_df_and_get_moving_average(df: DataFrame, dep_var: str, ind_var: str, n_bins: int = 10,
                                              start_point=None, end_point=None, na_value=np.nan):
    """
    This function will equally separate a dataframe and return the moving average of
    :param df: dataframe
    :param dep_var: dependent variable name
    :param ind_var: independent variable name
    :param n_bins: optional, How many bins is used to hold each value. Default is 10
    :param start_point: optional, the start point to cut. Default is the minimum of dep var
    :param end_point: optional, the start point to cut. Default is the maximum of dep var
    :param na_value: if no values exists, use which one to instead.
    :return: New dataframe contains all the values
    """
    if end_point is None:
        end_point = df[ind_var].max()
    if start_point is None:
        start_point = df[ind_var].min()

    step = (end_point - start_point) / n_bins

    result_row = list()
    for i in np.arange(start_point, end_point, step):
        i_id = i + step / 2
        if step > 0:
            dep_val = df[df[ind_var].apply(lambda x: i <= x < i + step)][dep_var].mean()
        else:
            dep_val = df[df[ind_var].apply(lambda x: i + step < x <= i)][dep_var].mean()
        result_row.append({ind_var: i_id, dep_var: dep_val if not np.isnan(dep_val) else na_value})

    result_df = DataFrame(result_row)
    return result_df


def draw_rdd_pictures(data_df, ind_var, dep_var, bin_num, bandwidth, order=1, x_label=None,
                      y_label=None, ax=None):
    sub_df: DataFrame = data_df.loc[:, [ind_var, dep_var, const.IS_WIN]].dropna(how='any')

    left_df = sub_df[sub_df[const.IS_WIN] < 0.5].copy()
    right_df = sub_df[sub_df[const.IS_WIN] > 0.5].copy()

    if ax is None:
        fig = plt.figure(figsize=(12, 5))
        ax = plt.subplot()
    left_tmp_df = evenly_separate_df_and_get_moving_average(df=left_df, dep_var=dep_var, ind_var=ind_var,
                                                            n_bins=bin_num, start_point=0.5, end_point=0 + bandwidth,
                                                            na_value=np.nan)
    right_tmp_df = evenly_separate_df_and_get_moving_average(df=right_df, dep_var=dep_var, ind_var=ind_var,
                                                             n_bins=bin_num, start_point=0.5, end_point=1 - bandwidth,
                                                             na_value=np.nan)
    ax = sns.regplot(x=ind_var, y=dep_var, data=left_df, ax=ax, x_bins=None, scatter=False,
                     color='black', truncate=True, x_ci=None, ci=95, order=order)
    ax = sns.regplot(x=ind_var, y=dep_var, data=right_df, ax=ax, x_bins=None, scatter=False,
                     color='black', truncate=True, x_ci=None, ci=95, order=order)
    ax = sns.regplot(x=ind_var, y=dep_var, data=left_df, ax=ax, x_bins=bin_num, scatter=True,
                     color='black', truncate=True, x_ci=None, fit_reg=False)
    ax = sns.regplot(x=ind_var, y=dep_var, data=right_df, ax=ax, x_bins=bin_num, scatter=True,
                     color='black', truncate=True, x_ci=None, fit_reg=False)

    ax.vlines(0.5, ax.get_ylim()[0], ax.get_ylim()[1])

    # set-up the plot
    ax.set_aspect('auto')
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    # ax.grid(b=True)
    return ax


def print_log(log_news):
    current_date_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{current_date_str}] {log_news}")
