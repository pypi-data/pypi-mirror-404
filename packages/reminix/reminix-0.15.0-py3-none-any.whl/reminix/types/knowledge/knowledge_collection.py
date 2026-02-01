# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["KnowledgeCollection"]


class KnowledgeCollection(BaseModel):
    id: str
    """Unique collection ID"""

    created_at: str = FieldInfo(alias="createdAt")
    """When the collection was created"""

    description: Optional[str] = None
    """Collection description"""

    embedding_model: str = FieldInfo(alias="embeddingModel")
    """Embedding model used"""

    name: str
    """Collection name"""

    project_id: str = FieldInfo(alias="projectId")
    """Project ID"""

    updated_at: str = FieldInfo(alias="updatedAt")
    """When the collection was last updated"""

    document_count: Optional[float] = FieldInfo(alias="documentCount", default=None)
    """Total number of documents"""

    ready_document_count: Optional[float] = FieldInfo(alias="readyDocumentCount", default=None)
    """Number of processed documents"""
