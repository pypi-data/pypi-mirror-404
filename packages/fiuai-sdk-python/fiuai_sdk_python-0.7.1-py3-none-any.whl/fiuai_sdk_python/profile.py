# -- coding: utf-8 --
# Project: fiuai_sdk_python
# Created Date: 2025 09 Th
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI


# -- coding: utf-8 --
# Project: response
# Created Date: 2025 05 Tu
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI


from pydantic import BaseModel, Field
from typing import List, Literal
from .utils.text import safe_string_name


class UserCompanyInfo(BaseModel):
    name: str = Field(description="公司id")
    full_name: str = Field(description="公司名称")

class UserBaseInfo(BaseModel):
    name: str = Field(description="用户名id")
    email: str = Field(description="邮箱")
    first_name: str = Field(description="名")
    full_name: str = Field(description="全名")
    language: str = Field(description="语言")
    time_zone: str = Field(description="时区")
    auth_tenant_id: str = Field(description="租户id")
    current_company: str = Field(description="当前公司")
    available_companies: List[UserCompanyInfo] = Field(description="用户在租户下可以访问的公司列表", default_factory=list)


class UserPermissionInfo(BaseModel):
    can_select: List[str] = Field(description="可以查询的文档", default_factory=list)
    can_read: List[str] = Field(description="可以读取的文档", default_factory=list)
    can_write: List[str] = Field(description="可以写入的文档", default_factory=list)
    can_create: List[str] = Field(description="可以创建的文档", default_factory=list)
    can_delete: List[str] = Field(description="可以删除的文档", default_factory=list)
    can_submit: List[str] = Field(description="可以提交的文档", default_factory=list)
    can_cancel: List[str] = Field(description="可以取消的文档", default_factory=list)
    can_search: List[str] = Field(description="可以搜索的文档", default_factory=list)

    # def __init__(self, user: str):
    #     super().__init__()
    
    # def can_select(self, doctype: str) -> bool:
    #     return doctype in self.can_select
    
    # def can_read(self, doctype: str) -> bool:
    #     return doctype in self.can_read
    
    # def can_write(self, doctype: str) -> bool:
    #     return doctype in self.can_write
    
    # def can_create(self, doctype: str) -> bool:
    #     return doctype in self.can_create
    
    # def can_delete(self, doctype: str) -> bool:
    #     return doctype in self.can_delete
    
    # def can_submit(self, doctype: str) -> bool:
    #     return doctype in self.can_submit
    
    # def can_cancel(self, doctype: str) -> bool:
    #     return doctype in self.can_cancel
    
    # def can_search(self, doctype: str) -> bool:
    #     return doctype in self.can_search
    
class UserTenantInfo(BaseModel):
    name: str = Field(description="租户id")
    tenant_name: str = Field(description="租户名称")


class UserCurrentCompanyInfo(BaseModel):
    name: str = Field(description="公司id")
    full_name: str = Field(description="公司名称")
    unique_no: str = Field(description="公司唯一编号")
    country_region: str = Field(description="国家")
    default_currency: str = Field(description="货币")
    company_size: str = Field(description="公司规模")
    entity_type: Literal["Enterprise", "Individual", "Other"] = Field(description="公司类型")
    company_profile: str = Field(description="公司业务特点提示词", default="")
    
class UserProfileInfo(BaseModel):
    user_base_info: UserBaseInfo = Field(description="用户基础信息")
    user_permissions: UserPermissionInfo = Field(description="用户权限")
    user_tenant_info: UserTenantInfo = Field(description="用户租户信息")
    user_current_company_info: UserCurrentCompanyInfo = Field(description="用户当前公司信息")
    
    
    def create_safe_name_profile(self) -> 'UserProfileInfo':

        """替换对象中的所有的name为安全字符串"""

        return UserProfileInfo(
            user_base_info=UserBaseInfo(
                name=safe_string_name(self.user_base_info.name),
                email=self.user_base_info.email,
                first_name=self.user_base_info.first_name,
                full_name=self.user_base_info.full_name,
                language=self.user_base_info.language,
                time_zone=self.user_base_info.time_zone,
                auth_tenant_id=self.user_base_info.auth_tenant_id,
                current_company=self.user_base_info.current_company,
                available_companies=self.user_base_info.available_companies,
            ),
            user_permissions=self.user_permissions,
            user_tenant_info=UserTenantInfo(
                name=self.user_tenant_info.name,
                tenant_name=safe_string_name(self.user_tenant_info.tenant_name),
            ),
            user_current_company_info=UserCurrentCompanyInfo(
                name=self.user_current_company_info.name,
                full_name=safe_string_name(self.user_current_company_info.full_name),
                unique_no=self.user_current_company_info.unique_no,
                country_region=self.user_current_company_info.country_region,
                default_currency=self.user_current_company_info.default_currency,
                company_size=self.user_current_company_info.company_size,
                entity_type=self.user_current_company_info.entity_type,
                company_profile=self.user_current_company_info.company_profile,
            ),
        )