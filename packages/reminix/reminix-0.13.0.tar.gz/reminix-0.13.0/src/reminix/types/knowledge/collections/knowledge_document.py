# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["KnowledgeDocument"]


class KnowledgeDocument(BaseModel):
    id: str
    """Unique document ID"""

    collection_id: str = FieldInfo(alias="collectionId")
    """Collection ID"""

    created_at: str = FieldInfo(alias="createdAt")
    """When the document was created"""

    mime_type: str = FieldInfo(alias="mimeType")
    """MIME type"""

    name: str
    """Document name"""

    source_url: str = FieldInfo(alias="sourceUrl")
    """S3 URL of the document"""

    status: Literal["pending", "processing", "ready", "failed"]
    """Processing status"""

    updated_at: str = FieldInfo(alias="updatedAt")
    """When the document was last updated"""

    metadata: Optional[object] = None
    """Document metadata"""
