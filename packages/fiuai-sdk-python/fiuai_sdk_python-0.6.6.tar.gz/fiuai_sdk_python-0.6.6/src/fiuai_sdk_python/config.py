# -- coding: utf-8 --
# Project: fiuai_sdk_python
# Created Date: 2026 01 Su
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2026 FiuAI


"""各类枚举值"""

from pydantic import BaseModel, Field
from enum import Enum, StrEnum


class CompanyNetworkConnectionType(StrEnum):
    """公司网络连接类型"""
    Customer = "Customer"
    Supplier = "Supplier"


class CompanySize(StrEnum):
    """公司规模"""
    One = "1"
    TwoToFifteen = "2-15"
    SixteenToFortyNine = "16-49"
    FiftyToNinetyNine = "50-99"
    MoreThanOneHundred = "100-249"
    MoreThanTwoHundredFifty = "250-499"
    MoreThanFiveHundred = "500-999"
    MoreThanOneThousand = "1000+"



class CompanyEntityType(StrEnum):
    """公司实体类型"""
    Enterprise = "Enterprise"
    Individual = "Individual"
    Other = "Other"
