# -- coding: utf-8 --
# Project: utils
# Created Date: 2025 11 Fr
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI

from urllib.parse import quote_plus

# 全角符号，括号，横线，标点符号等
FULL_WIDTH_CHARACTERS = {
    "！": "!",
    "？": "?",
    "；": ";",
    "，": ",",
    "。": ".",
    "、": ",",
    "（": "(",
    "）": ")",
    "【": "[",
    "】": "]",
    "《": "<",
    "》": ">",
    "：": ":",
    "“": "\"",
    "”": "\"",
    "‘": "'",
    "’": "'",
    "-": "-",
}




def safe_string_name(name: str) -> str:
    """
    清理文本中的特殊字符, 用于公司名称、银行名称等文本标准化
    """
    for char, full_width_char in FULL_WIDTH_CHARACTERS.items():
        name = name.replace(char, full_width_char)
    return name


def safe_str(s: str) -> str:
    """安全处理字符串，对特殊字符进行URL编码
    
    用于处理Redis密码等可能包含特殊字符的字符串，
    确保在URL中使用时不会引起解析错误
    
    Args:
        s: 需要处理的字符串
        
    Returns:
        str: URL编码后的安全字符串
    """
    if not s:
        return s
    # 使用 quote_plus 对所有字符进行编码，包括 # 等特殊字符
    # safe='' 表示不保留任何字符为安全字符，全部进行编码
    return quote_plus(s, safe='')


def safe_json_str(s: str) -> str:


    # 将非法的控制字符替换为 \n 或删除
    s = s.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
    # 或者更严格地过滤
    # s = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', s)  # 移除控制字符
    return s