#!/usr/bin/env python

# -*- coding: utf-8 -*-
# @Filename: path_info
# @Date: 2024/8/12
# @Author: Mark Wang
# @Email: wangyouan@gamil.com


import os


class PathInfo(object):
    if hasattr(os, 'uname') and os.uname().nodename == 'wyaamd-server001':
        ROOT_PATH = '/home/user/projects/STOCKAct'
        DATABASE_PATH = '/home/user/data'
    else:
        ROOT_PATH = r'D:\Onedrive\Temp\Projects\STOCKAct'
        DATABASE_PATH = r'D:\Onedrive\Documents\data'

    TEMP_PATH = os.path.join(ROOT_PATH, 'temp')
    RESULT_PATH = os.path.join(ROOT_PATH, 'regression_data')
    DATA_PATH = os.path.join(ROOT_PATH, 'data')
    REGRESSION_RESULT_PATH = os.path.join(ROOT_PATH, 'regression_results')

    COMPUSTAT_PATH = os.path.join(DATABASE_PATH, 'compustat')
