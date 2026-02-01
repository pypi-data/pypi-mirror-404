# -- coding: utf-8 --
# Project: fiuaiapp
# Created Date: 2025-01-20
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI

from typing import Literal
from enum import StrEnum


class DocFieldType(StrEnum):
    """doctype 定义的字段类型"""
    
    #  常用 
    Data: str = "Data"
    Check: str = "Check"
    # currency 类似float
    Currency: str = "Currency"
    Time: str = "Time"
    Date: str = "Date"
    Datetime: str = "Datetime"
    Int: str = "Int"
    Float: str = "Float"
    Select: str = "Select"
    Link: str = "Link"
    Text: str = "Text"
    Long_Text: str = "Long Text"
    Table: str = "Table"

    # 其他不常见基础字段类型
    Autocomplete: str = "Autocomplete"
    Attach: str = "Attach"
    Attach_Image: str = "Attach Image"
    Barcode: str = "Barcode"
    Button: str = "Button"
    Code: str = "Code"
    Color: str = "Color"
    Column_Break: str = "Column Break"
    
   
    
    
    Duration: str = "Duration"
    Dynamic_Link: str = "Dynamic Link"
    
    Fold: str = "Fold"
    Geolocation: str = "Geolocation"
    Heading: str = "Heading"
    Html: str = "HTML"
    Html_Editor: str = "HTML Editor"
    Icon: str = "Icon"
    Image: str = "Image"
    
    Json: str = "JSON"
    
   
    Markdown_Editor: str = "Markdown Editor"
    Password: str = "Password"
    Percent: str = "Percent"
    Phone: str = "Phone"
    Read_Only: str = "Read Only"
    Rating: str = "Rating"
    Section_Break: str = "Section Break"
    
    Signature: str = "Signature"
    Small_Text: str = "Small Text"
    Tab_Break: str = "Tab Break"
    
    Table_Multi_Select: str = "Table MultiSelect"
    
    Text_Editor: str = "Text Editor"


    def to_db_column_type(self, db_engine: Literal["mysql", "postgresql"] = "postgresql") -> str:
        """
        根据frappe的字段类型返回对应的数据库列类型
        Args:
            db_engine: 数据库引擎, 默认postgresql
        Returns:
            str: 数据库列类型
        """
        if db_engine != "postgresql":
            raise ValueError(f"{db_engine} is not supported")
            
        match self:
            # 基本数据类型
            case DocFieldType.Data:
                return "varchar"
            case DocFieldType.Int:
                return "integer"
            case DocFieldType.Float:
                return "numeric"
            case DocFieldType.Check:
                return "boolean"
            
            # 文本类型
            case DocFieldType.Text:
                return "text"
            case DocFieldType.Long_Text:
                return "text"
            case DocFieldType.Small_Text:
                return "text"
            case DocFieldType.Code:
                return "text"
            case DocFieldType.Html:
                return "text"
            case DocFieldType.Html_Editor:
                return "text"
            case DocFieldType.Markdown_Editor:
                return "text"
            case DocFieldType.Text_Editor:
                return "text"
            case DocFieldType.Password:
                return "varchar"
            case DocFieldType.Select:
                return "varchar"
            case DocFieldType.Autocomplete:
                return "varchar"
            
            # 日期时间类型
            case DocFieldType.Date:
                return "date"
            case DocFieldType.Datetime:
                return "timestamp"
            case DocFieldType.Time:
                return "time"
            case DocFieldType.Duration:
                return "bigint"  # 通常存储为秒数
            
            # 数值类型（带精度）
            case DocFieldType.Currency:
                return "numeric"
            case DocFieldType.Percent:
                return "numeric"
            
            # 链接类型
            case DocFieldType.Link:
                return "varchar"
            case DocFieldType.Dynamic_Link:
                return "varchar"
            
            # 文件/附件类型
            case DocFieldType.Attach:
                return "varchar"
            case DocFieldType.Attach_Image:
                return "varchar"
            case DocFieldType.Image:
                return "varchar"
            case DocFieldType.Signature:
                return "text"
            
            # 其他类型
            case DocFieldType.Color:
                return "varchar"
            case DocFieldType.Barcode:
                return "varchar"
            case DocFieldType.Phone:
                return "varchar"
            case DocFieldType.Icon:
                return "varchar"
            case DocFieldType.Rating:
                return "integer"
            case DocFieldType.Json:
                return "jsonb"
            case DocFieldType.Geolocation:
                return "varchar"  # 或 jsonb，根据实际存储格式
            
            # 表类型
            case DocFieldType.Table:
                return "varchar"  # 存储子表名称引用
            case DocFieldType.Table_Multi_Select:
                return "text"  # 通常以JSON格式存储
            
            # 布局类型（通常不存储在数据库中，但为了完整性返回varchar）
            case DocFieldType.Button:
                return "varchar"
            case DocFieldType.Column_Break:
                return "varchar"
            case DocFieldType.Fold:
                return "varchar"
            case DocFieldType.Heading:
                return "varchar"
            case DocFieldType.Section_Break:
                return "varchar"
            case DocFieldType.Tab_Break:
                return "varchar"
            case DocFieldType.Read_Only:
                return "varchar"
            
            # 默认情况
            case _:
                return "varchar"
    
    def to_pandas_dtype(self) -> "Dtype":
        """
        将字段类型转换为 pandas 的 dtype
        Returns:
            Dtype: pandas 的 dtype 枚举
        """
        match self:
            # 整数类型
            case DocFieldType.Int:
                return Dtype.Int64  # 使用可空整数类型，支持 NaN
            # 浮点数类型
            case DocFieldType.Float:
                return Dtype.Float64
            case DocFieldType.Currency:
                return Dtype.Float64
            case DocFieldType.Percent:
                return Dtype.Float64
            # 布尔类型
            case DocFieldType.Check:
                return Dtype.Boolean
            # 日期时间类型
            case DocFieldType.Date:
                return Dtype.Datetime64
            case DocFieldType.Datetime:
                return Dtype.Datetime64
            case DocFieldType.Time:
                return Dtype.Object  # pandas 没有专门的 time dtype，使用 object
            case DocFieldType.Duration:
                return Dtype.Timedelta64
            # 表类型
            case DocFieldType.Table:
                return Dtype.Object  # 子表数据通常存储为对象或 JSON
            # 其他类型（字符串、文本等）
            case _:
                return Dtype.Object  # 默认返回 object 类型（字符串、文本等）


class Dtype(StrEnum):
    """pandas 的 dtype 枚举类型"""
    
    # 整数类型
    Int64 = "Int64"  # 可空整数类型，支持 NaN
    Int32 = "Int32"  # 可空整数类型（32位）
    
    # 浮点数类型
    Float64 = "float64"
    Float32 = "float32"
    
    # 布尔类型
    Boolean = "boolean"
    
    # 日期时间类型
    Datetime64 = "datetime64[ns]"
    Timedelta64 = "timedelta64[ns]"
    
    # 对象类型（字符串、文本、复杂对象等）
    Object = "object"
    
    # 字符串类型（pandas 1.0+）
    String = "string"
    
    def to_docfield_type(self) -> DocFieldType:
        """
        将 pandas 的 dtype 转换为 DocFieldType
        Returns:
            DocFieldType: 对应的文档字段类型枚举
        """
        match self:
            # 整数类型 -> Int
            case Dtype.Int64 | Dtype.Int32:
                return DocFieldType.Int
            # 浮点数类型 -> Float
            case Dtype.Float64 | Dtype.Float32:
                return DocFieldType.Float
            # 布尔类型 -> Check
            case Dtype.Boolean:
                return DocFieldType.Check
            # 日期时间类型 -> Date 或 Datetime
            case Dtype.Datetime64:
                return DocFieldType.Datetime
            # 时长类型 -> Duration
            case Dtype.Timedelta64:
                return DocFieldType.Duration
            # 字符串类型 -> Data
            case Dtype.String:
                return DocFieldType.Data
            # 对象类型（默认）-> Data
            case _:
                return DocFieldType.Data


