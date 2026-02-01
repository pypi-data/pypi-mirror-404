# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from pydantic import Field as FieldInfo

from ...._models import BaseModel
from .knowledge_document import KnowledgeDocument

__all__ = ["DocumentUploadResponse"]


class DocumentUploadResponse(BaseModel):
    document: KnowledgeDocument

    upload_url: str = FieldInfo(alias="uploadUrl")
    """Presigned URL for uploading the file"""
