#!/usr/bin/env python

# -*- coding: utf-8 -*-
# @Filename: __init__.py
# @Date: 2024/10/9
# @Author: Mark Wang
# @Email: wangyouan@gamil.com

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