# -- coding: utf-8 --
# Project: fiuai_sdk_python
# Created Date: 2025 12 Mo
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI


from typing import List, Dict, Optional 
from pydantic import BaseModel, Field
from logging import getLogger

from .client import FiuaiSDK
from .type import DocTypeMeta
from .datatype import DocFieldType
from .setup import load_doctype_meta

logger = getLogger(__name__)

class DoctypeLinkInfo(BaseModel):
    name: str = Field(description="链接文档类型名称,比如Customer,Supplier,etc.")
    join_key: str = Field(description="主文档关联其他文档的字段名称")

class DoctypeChildInfo(BaseModel):
    name: str = Field(description="子文档类型名称")
    join_key: str = Field(description="主文档关联子文档的字段名称")

class DoctypeInfo(BaseModel):
    name: str = Field(description="文档类型名称,比如Invoice,Purchase Order,etc.")
    doctype_prompts: Optional[str] = Field(description="文档类型对应的prompt")
    link_doctypes: List[DoctypeLinkInfo] = Field(default=[], description="文档类型包含的所有Link文档类型")
    child_doctypes: List[DoctypeChildInfo] = Field(default=[], description="文档类型包含的所有Child文档类型")


class DoctypeOverview(BaseModel):
    doctypes: Dict[str, DoctypeInfo] = Field(default={}, description="文档类型列表")



def _get_doctypes(
        client: FiuaiSDK, 
        limit_start: int, 
        limit_page_length: int,
        fields: List[str], 
        filters: List[List[str]],
        only_has_prompt: bool
    ) -> List[DoctypeInfo]:
    """
    获取指定文档类型
    """

    d = []
    
    if only_has_prompt:
        filters.append(["doctype_prompts", "!=", ""])


    doctypes = client.internal_get_list(
        doctype="DocType",
        fields=fields,
        filters=filters,
        limit_start=limit_start,
        limit_page_length=limit_page_length,
    )

    if not doctypes.is_success():
        logger.error(f"get doctypes failed: {doctypes.error_message}")
        return []

    return [DoctypeInfo(name=doctype["name"], doctype_prompts=doctype["doctype_prompts"]) for doctype in doctypes.data]



def get_all_doctype_from_platforom(client: FiuaiSDK, only_has_prompt: bool = True) -> List[DocTypeMeta]:
    """
    获取所有文档类型
    """
    
    all_doctypes = []

    limit_start = 0
    limit_page_length = 20
    logger.info(f"get all doctypes from platform, limit_start: {limit_start}, limit_page_length: {limit_page_length}")
    while True:
        doctypes = _get_doctypes(
            client, 
            limit_start=limit_start, 
            limit_page_length=limit_page_length,
            fields=["name", "doctype_prompts"],
            filters=[],
            only_has_prompt=only_has_prompt,
        )
        if not doctypes:
            break

        all_doctypes.extend(doctypes)
        limit_start += limit_page_length

    logger.info(f"get all doctypes from platform, total: {len(all_doctypes)}")

    return all_doctypes


def _get_linked_doctypes_info(meta: DocTypeMeta, only_has_prompt: bool = True) -> List[DoctypeLinkInfo]:
    """
    获取链接的文档类型信息
    """
    d = []
    for field in meta.fields:
        if field.fieldtype == DocFieldType.Link:
            if only_has_prompt and ( not field.field_prompt or field.field_prompt == "" ):
                continue
            d.append(DoctypeLinkInfo(name=field.options[0], join_key=field.fieldname))
    return d

def _get_child_doctypes_info(meta: DocTypeMeta, only_has_prompt: bool = True) -> List[DoctypeChildInfo]:
    """
    获取子文档类型信息
    """
    d = []
    for field in meta.fields:
        if field.fieldtype == DocFieldType.Table:
            if only_has_prompt and ( not field.field_prompt or field.field_prompt == "" ):
                continue
            d.append(DoctypeChildInfo(name=field.options[0], join_key=field.fieldname))
    return d

def get_platform_doctype_overview(client: FiuaiSDK, only_has_prompt: bool = True) -> DoctypeOverview:
    """
    获取文档类型概览
    """

    
    all_doctypes = get_all_doctype_from_platforom(client, only_has_prompt)

    d = { _doctype.name: _doctype for _doctype in all_doctypes }

    if not d :
        return DoctypeOverview(doctypes={})


    for _doctype in all_doctypes:

        resp = load_doctype_meta(client, _doctype.name, only_has_prompt=only_has_prompt)
        if not resp:
            raise Exception(f"get_doctype_overview get meta failed: {_doctype.name}")

        linked_doctypes_info = _get_linked_doctypes_info(resp, only_has_prompt)
        child_doctypes_info = _get_child_doctypes_info(resp, only_has_prompt)


        d[_doctype.name] = DoctypeInfo(
            name=_doctype.name,
            doctype_prompts=_doctype.doctype_prompts,
            link_doctypes=linked_doctypes_info,
            child_doctypes=child_doctypes_info,
        )
    

    return DoctypeOverview(doctypes=d)