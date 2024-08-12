#!/usr/bin/env python

# -*- coding: utf-8 -*-
# @Filename: path_info
# @Date: 2024/8/12
# @Author: Mark Wang
# @Email: wangyouan@gamil.com


import os


class PathInfo(object):
    ROOT_PATH = r'D:\Onedrive\Temp\Projects\STOCKAct'
    TEMP_PATH = os.path.join(ROOT_PATH, 'temp')
    RESULT_PATH = os.path.join(ROOT_PATH, 'output')
    DATA_PATH = os.path.join(ROOT_PATH, 'data')

    DATABASE_PATH = r'D:\Onedrive\Documents\data'
    COMPUSTAT_PATH = os.path.join(DATABASE_PATH, 'compustat')
