# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["AgentKnowledgeBaseConfig"]


class AgentKnowledgeBaseConfig(BaseModel):
    """Knowledge base feature configuration"""

    collection_ids: List[str] = FieldInfo(alias="collectionIds")
    """Collection IDs to search"""

    enabled: bool
    """Whether knowledge base is enabled for this agent"""
